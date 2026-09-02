#!/usr/bin/env python3
"""Raw XMPP probe for the MIX behaviour this patch series changes.

Runs against a loopback or otherwise trusted server over plaintext C2S and
checks, in order:

  1. the account advertises urn:xmpp:mix:pam:2 in disco#info;
  2. the MIX service advertises urn:xmpp:mix:core:1;
  3. a throwaway channel can be created;
  4. the information node is readable BEFORE joining (patch 0001,
     non-hidden channel discovery read);
  5. a PAM client-join asking for messages, participants and info returns
     a result in urn:xmpp:mix:pam:2 whose inner join lists the info node
     (patch 0001);
  6. the information node item carries FORM_TYPE urn:xmpp:mix:core:1, Name
     and Contact (patch 0001);
  7. a groupchat submission is echoed immediately with Core 1 metadata and
     the submission id (patches 0002 and 0003);
  8. channel MAM returns the same message with Core 1 metadata;
  9. client-leave and channel destroy succeed, leaving no state behind.

Credentials come from the environment only; nothing is written to disk.

  MIX_PROBE_HOST      default 127.0.0.1
  MIX_PROBE_PORT      default 5222
  MIX_PROBE_DOMAIN    default localhost
  MIX_PROBE_USER      localpart of an existing account (required)
  MIX_PROBE_PASSWORD  its password (required)
  MIX_PROBE_SERVICE   default mix.<domain>

Exit status 0 on PASS, 1 with the failing step named on FAIL.
"""

from __future__ import annotations

import base64
import os
import re
import socket
import sys
import time
from xml.sax.saxutils import escape

HOST = os.environ.get("MIX_PROBE_HOST", "127.0.0.1")
PORT = int(os.environ.get("MIX_PROBE_PORT", "5222"))
DOMAIN = os.environ.get("MIX_PROBE_DOMAIN", "localhost")
USER = os.environ.get("MIX_PROBE_USER", "")
PASSWORD = os.environ.get("MIX_PROBE_PASSWORD", "")
SERVICE = os.environ.get("MIX_PROBE_SERVICE", f"mix.{DOMAIN}")

NS_CORE_1 = b"urn:xmpp:mix:core:1"
NS_PAM_2 = b"urn:xmpp:mix:pam:2"
NODE_INFO = "urn:xmpp:mix:nodes:info"


class XmppStream:
    def __init__(self) -> None:
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        self.buffer = b""

    def send(self, xml: str) -> None:
        self.sock.sendall(xml.encode("utf-8"))

    def receive_until(self, *needles: bytes, timeout: float = 8) -> bytes:
        deadline = time.monotonic() + timeout
        while not all(needle in self.buffer for needle in needles):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    "timed out waiting for "
                    + ", ".join(n.decode("utf-8", "replace") for n in needles)
                )
            self.sock.settimeout(remaining)
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("XMPP socket closed")
            self.buffer += chunk
        data, self.buffer = self.buffer, b""
        return data

    def iq(self, iq_id: str, xml: str, *extra: bytes, timeout: float = 8) -> bytes:
        self.send(xml)
        return self.receive_until(iq_id.encode(), *extra, timeout=timeout)

    def open(self) -> None:
        self.send(
            f"<stream:stream to='{DOMAIN}' version='1.0' xmlns='jabber:client' "
            "xmlns:stream='http://etherx.jabber.org/streams'>"
        )
        self.receive_until(b"</stream:features>")

    def close(self) -> None:
        try:
            self.send("</stream:stream>")
        finally:
            self.sock.close()


def is_result(data: bytes, iq_id: str) -> bool:
    return re.search(
        rb"<iq[^>]*id=['\"]" + re.escape(iq_id.encode()) + rb"['\"][^>]*type=['\"]result['\"]",
        data,
    ) is not None or re.search(
        rb"<iq[^>]*type=['\"]result['\"][^>]*id=['\"]" + re.escape(iq_id.encode()) + rb"['\"]",
        data,
    ) is not None


def field_values(form: bytes, var: str) -> list[bytes]:
    match = re.search(
        rb"<field[^>]*var=['\"]" + re.escape(var.encode()) + rb"['\"][^>]*>(.*?)</field>",
        form,
        re.S,
    )
    if not match:
        return []
    return re.findall(rb"<value>(.*?)</value>", match.group(1), re.S)


def main() -> int:
    if not USER or not PASSWORD:
        print("set MIX_PROBE_USER and MIX_PROBE_PASSWORD", file=sys.stderr)
        return 2
    bare_jid = f"{USER}@{DOMAIN}"
    stamp = int(time.time())
    channel_name = f"probe-{stamp}-{os.getpid()}"
    channel = f"{channel_name}@{SERVICE}"
    probe_text = f"mix-probe-{stamp}"
    stream = XmppStream()
    stage = "connect"
    created = False
    joined = False
    try:
        stage = "open stream"
        stream.open()
        stage = "authenticate (SASL PLAIN)"
        plain = base64.b64encode(b"\x00" + USER.encode() + b"\x00" + PASSWORD.encode()).decode()
        stream.send(f"<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>{plain}</auth>")
        if b"<success" not in stream.receive_until(b"success"):
            raise RuntimeError("SASL PLAIN did not succeed")
        stream.open()
        stage = "bind resource"
        bound = stream.iq(
            "p-bind",
            "<iq type='set' id='p-bind'><bind xmlns='urn:ietf:params:xml:ns:xmpp-bind'>"
            f"<resource>mix-probe-{os.getpid()}</resource></bind></iq>",
        )
        if not is_result(bound, "p-bind"):
            raise RuntimeError("bind failed")
        stream.send("<presence/>")

        stage = "1 account advertises PAM 2"
        disco = stream.iq(
            "p-disco-acct",
            f"<iq to='{bare_jid}' type='get' id='p-disco-acct'>"
            "<query xmlns='http://jabber.org/protocol/disco#info'/></iq>",
        )
        if NS_PAM_2 not in disco:
            raise RuntimeError("account disco#info lacks urn:xmpp:mix:pam:2")

        stage = "2 service advertises Core 1"
        disco = stream.iq(
            "p-disco-svc",
            f"<iq to='{SERVICE}' type='get' id='p-disco-svc'>"
            "<query xmlns='http://jabber.org/protocol/disco#info'/></iq>",
        )
        if NS_CORE_1 not in disco:
            raise RuntimeError("service disco#info lacks urn:xmpp:mix:core:1")

        stage = "3 create throwaway channel"
        made = stream.iq(
            "p-create",
            f"<iq to='{SERVICE}' type='set' id='p-create'>"
            f"<create channel='{channel_name}' xmlns='urn:xmpp:mix:core:1'/></iq>",
        )
        if not is_result(made, "p-create"):
            raise RuntimeError("channel create failed")
        created = True

        stage = "4 info node readable before join (non-hidden channel)"
        info = stream.iq(
            "p-info-prejoin",
            f"<iq to='{channel}' type='get' id='p-info-prejoin'>"
            f"<pubsub xmlns='http://jabber.org/protocol/pubsub'><items node='{NODE_INFO}'/></pubsub></iq>",
        )
        if not is_result(info, "p-info-prejoin"):
            raise RuntimeError("info node read before join was refused")

        stage = "5 PAM join returns pam:2 with info node negotiated"
        join = stream.iq(
            "p-join",
            f"<iq to='{bare_jid}' type='set' id='p-join'>"
            f"<client-join channel='{channel}' xmlns='urn:xmpp:mix:pam:2'>"
            "<join xmlns='urn:xmpp:mix:core:1'><nick>probe</nick>"
            "<subscribe node='urn:xmpp:mix:nodes:messages'/>"
            "<subscribe node='urn:xmpp:mix:nodes:participants'/>"
            f"<subscribe node='{NODE_INFO}'/>"
            "</join></client-join></iq>",
            b"client-join",
            timeout=10,
        )
        if not is_result(join, "p-join"):
            raise RuntimeError("PAM join did not return a result")
        joined = True
        result_el = re.search(rb"<client-join[^>]*>", join)
        if not result_el or NS_PAM_2 not in result_el.group(0):
            raise RuntimeError("client-join result is not in urn:xmpp:mix:pam:2")
        if re.search(rb"<subscribe[^>]*node=['\"]" + NODE_INFO.encode() + rb"['\"]", join) is None:
            raise RuntimeError("join result does not list the info node")

        stage = "6 info node form has FORM_TYPE core:1, Name, Contact"
        info = stream.iq(
            "p-info",
            f"<iq to='{channel}' type='get' id='p-info'>"
            f"<pubsub xmlns='http://jabber.org/protocol/pubsub'><items node='{NODE_INFO}'/></pubsub></iq>",
        )
        if not is_result(info, "p-info"):
            raise RuntimeError("info node read after join failed")
        if field_values(info, "FORM_TYPE") != [NS_CORE_1]:
            raise RuntimeError("FORM_TYPE is not urn:xmpp:mix:core:1")
        if field_values(info, "Name") != [channel_name.encode()]:
            raise RuntimeError("Name field does not carry the channel name")
        if not field_values(info, "Contact"):
            raise RuntimeError("Contact field missing")

        stage = "7 groupchat echo carries Core 1 and the submission id"
        stream.send(
            f"<message to='{channel}' type='groupchat' id='{probe_text}'>"
            f"<body>{escape(probe_text)}</body></message>"
        )
        echo = stream.receive_until(probe_text.encode(), b"<mix", timeout=10)
        mix_el = re.search(rb"<mix[^>]*>", echo)
        if not mix_el or NS_CORE_1 not in mix_el.group(0):
            raise RuntimeError("echo <mix> element is not urn:xmpp:mix:core:1")
        if b"submission-id" not in echo:
            raise RuntimeError("echo lacks submission-id")

        stage = "8 channel MAM returns the message with Core 1"
        history = stream.iq(
            "p-mam",
            f"<iq to='{channel}' type='set' id='p-mam'>"
            "<query xmlns='urn:xmpp:mam:2' queryid='p-mam-q'>"
            "<set xmlns='http://jabber.org/protocol/rsm'><max>20</max><before/></set>"
            "</query></iq>",
            probe_text.encode(),
            timeout=10,
        )
        if NS_CORE_1 not in history or b"urn:xmpp:mam:2" not in history:
            raise RuntimeError("MAM result lacks Core 1 metadata")

        stage = "9 leave and destroy"
        left = stream.iq(
            "p-leave",
            f"<iq to='{bare_jid}' type='set' id='p-leave'>"
            f"<client-leave channel='{channel}' xmlns='urn:xmpp:mix:pam:2'>"
            "<leave xmlns='urn:xmpp:mix:core:1'/></client-leave></iq>",
            timeout=10,
        )
        if not is_result(left, "p-leave"):
            raise RuntimeError("client-leave failed")
        joined = False
        gone = stream.iq(
            "p-destroy",
            f"<iq to='{SERVICE}' type='set' id='p-destroy'>"
            f"<destroy channel='{channel_name}' xmlns='urn:xmpp:mix:core:1'/></iq>",
        )
        if not is_result(gone, "p-destroy"):
            raise RuntimeError("channel destroy failed")
        created = False
        print(f"PASS: all 9 MIX checks against {HOST}:{PORT} ({DOMAIN}, {SERVICE})")
        return 0
    except Exception as exc:  # noqa: BLE001 - report every failure with its stage
        tail = stream.buffer[-800:].decode("utf-8", "replace")
        print(f"FAIL at step: {stage}: {exc}", file=sys.stderr)
        if tail:
            print(f"last server data: {tail}", file=sys.stderr)
        return 1
    finally:
        if joined:
            try:
                stream.iq(
                    "p-leave-cleanup",
                    f"<iq to='{bare_jid}' type='set' id='p-leave-cleanup'>"
                    f"<client-leave channel='{channel}' xmlns='urn:xmpp:mix:pam:2'>"
                    "<leave xmlns='urn:xmpp:mix:core:1'/></client-leave></iq>",
                )
            except Exception:  # noqa: BLE001
                pass
        if created:
            try:
                stream.iq(
                    "p-destroy-cleanup",
                    f"<iq to='{SERVICE}' type='set' id='p-destroy-cleanup'>"
                    f"<destroy channel='{channel_name}' xmlns='urn:xmpp:mix:core:1'/></iq>",
                )
            except Exception:  # noqa: BLE001
                pass
        stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
