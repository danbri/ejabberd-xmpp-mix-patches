IMAGE ?= localhost/foafmixer/ejabberd-mix:26.07-pilot

.PHONY: image up down status logs register

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
