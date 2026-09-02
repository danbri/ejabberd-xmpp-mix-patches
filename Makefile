IMAGE ?= localhost/foafmixer/ejabberd-mix:26.07-pilot

.PHONY: image up down status logs register probe

image:
	MIX_IMAGE="$(IMAGE)" ./tools/build-image.sh

up:
	MIX_IMAGE="$(IMAGE)" ./tools/local-stack.sh up

down:
	MIX_IMAGE="$(IMAGE)" ./tools/local-stack.sh down

status:
	MIX_IMAGE="$(IMAGE)" ./tools/local-stack.sh status

logs:
	MIX_IMAGE="$(IMAGE)" ./tools/local-stack.sh logs

register:
	MIX_IMAGE="$(IMAGE)" ./tools/local-stack.sh register

# Raw protocol probe of the patched behaviour against the local review server.
# Prompts for an existing reviewer account; nothing is written to disk.
probe:
	@read -r -p "Account localpart: " u; \
	read -r -s -p "Password (input hidden): " p; printf '\n'; \
	MIX_PROBE_DOMAIN="$${MIX_DOMAIN:-localhost}" MIX_PROBE_USER="$$u" MIX_PROBE_PASSWORD="$$p" \
	  python3 ./tools/mix-probe.py
