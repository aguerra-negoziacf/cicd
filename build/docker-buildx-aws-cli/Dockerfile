ARG BUILDX_VERSION=0.8.0
ARG DOCKER_VERSION=20.10

FROM docker/buildx-bin:${BUILDX_VERSION} as buildx-bin
FROM docker:${DOCKER_VERSION}

COPY --from=buildx-bin /buildx /usr/libexec/docker/cli-plugins/docker-buildx

RUN apk add --update --no-cache \
  curl jq python3 py3-pip git && \
  pip install awscli