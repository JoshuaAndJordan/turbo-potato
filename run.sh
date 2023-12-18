#!/usr/bin/env bash

this_path="$(pwd)"
path="$(basename $this_path)"


docker build -t code_format -f code_format.dockerfile .
docker build -t kickstart -f kickstart.dockerfile .

docker run -it --privileged --device=/dev/kvm --network host \
  -v "`pwd`:/src/" --workdir "/src/" --restart=unless-stopped \
  --entrypoint "" "$1" bash

string="$(docker container ls | tail -n +2)"
id="$(echo "$string" | awk '{print $1}')"
if [ -n "$id" ]; then
  echo "Removing container with ID: $id"
  docker container stop $id
  docker container rm $id
fi

