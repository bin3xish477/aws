# stage 1
FROM alpine as build
RUN apk add go git
RUN go env -w GOPROXY=direct GOOS=linux GOARCH=amd64
ADD go.mod go.sum ./
RUN go mod download 
ADD . .
RUN go build -o /main

# stage 2
FROM clamav/clamav:latest
WORKDIR /app
COPY --from=build /main .
RUN freshclam
ENTRYPOINT [ "./main" ]
