REPO_OWNER:='reminiscence'
MULTIARCH:=false
ARCHS:=linux/amd64
ifeq ($(MULTIARCH), true)
	ARCHS:=linux/amd64,linux/arm/v7,linux/arm64/v8,linux/ppc64le,linux/s390x,linux/386
endif
VERSION:='latest'

all: setup build

setup:
	@./buildx.sh
clean:
	@sudo rm -rf logs db archive static/admin static/rest_framework
build: clean
	docker buildx build $(ENV) \
	--platform $(ARCHS) \
	--push --tag $(REPO_OWNER)/reminiscence:$(VERSION) .
