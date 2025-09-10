To build a new hadnoff base image Ver 0.X,
$ cd handoff/handoff/services/container/docker
$ docker build -t public.ecr.aws/m5u3u5p2/handoff-base:0.X . -f Dockerfile_base

Push the image to a public repository:
https://docs.aws.amazon.com/AmazonECR/latest/public/getting-started-cli.html
