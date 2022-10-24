package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
)

func handler(ctx context.Context, s3Event events.S3Event) {
	records := s3Event.Records
	for _, record := range records {
		bucket := record.S3.Bucket.Name
		region := record.AWSRegion
		key := record.S3.Object.Key

		sess, _ := session.NewSession(&aws.Config{
			Region: aws.String(region)},
		)

		downloader := s3manager.NewDownloader(sess)

		file, err := os.Create(fmt.Sprintf("/tmp/%s", key))
		if err != nil {
			continue
		}
		_, err = downloader.Download(file,
			&s3.GetObjectInput{
				Bucket: aws.String(bucket),
				Key:    aws.String(key),
			})
		if err != nil {
			fmt.Printf("unable to download file: %s", key)
			continue
		}
	}

	scan := exec.Command("/usr/bin/clamscan", []string{
		"--database=/var/lib/clamav",
	}...)

	scan.Run()
}

func main() {
	lambda.Start(handler)
}
