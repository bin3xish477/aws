FROM clamav/clamav:latest as clamav_build


FROM public.ecr.aws/lambda/provided:al2 as go_build
# install compiler
RUN yum install -y golang
RUN go env -w GOPROXY=direct
# cache dependencies
ADD go.mod go.sum ./
RUN go mod download
# build
ADD . .
RUN go build -o /main

FROM public.ecr.aws/lambda/provided:al2
COPY --from=go_build /main /main
ENTRYPOINT [ "/main" ]

