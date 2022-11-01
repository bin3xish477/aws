package main

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io/ioutil"
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
	for _, record := range s3Event.Records {
		bucket := record.S3.Bucket.Name
		//fmt.Println(bucket)
		region := record.AWSRegion
		//fmt.Println(region)
		key := record.S3.Object.Key
		//fmt.Println(key)

		sess, _ := session.NewSession(&aws.Config{
			Region: aws.String(region)},
		)
		downloader := s3manager.NewDownloader(sess)
		tmpFile := fmt.Sprintf("/tmp/%s", key)

		fmt.Printf("[+] writing file to %s\n", tmpFile)
		file, err := os.Create(tmpFile)
		if err != nil {
			fmt.Printf("[-] %s\n", err.Error())
			continue
		}

		files, _ := ioutil.ReadDir("/tmp")
		for _, file := range files {
			fmt.Printf("[+] file found in /tmp: %s\n", file.Name())
		}

		_, err = downloader.Download(file,
			&s3.GetObjectInput{
				Bucket: aws.String(bucket),
				Key:    aws.String(key),
			})
		if err != nil {
			fmt.Printf("[-] unable to download file %s because: %s\n", key, err.Error())
			continue
		}
		fmt.Printf("[+] file downloaded to %s...\n", tmpFile)

		if _, err := os.Stat("/usr/bin/clamscan"); errors.Is(err, os.ErrNotExist) {
			fmt.Println("[-] clamscan binary is not located in /usr/bin/clamscan")
			return
		} else {
			fmt.Printf("[+] clamscan was found in /usr/bin/...\n")
		}

		var stdout, stderr bytes.Buffer
		scan := exec.Command("/usr/bin/clamscan", []string{
			"--database=/var/lib/clamav",
			tmpFile,
		}...)

		var exitCode int

		scan.Stdout = &stdout
		scan.Stderr = &stderr
		if err := scan.Run(); err != nil {
			if exitErr, ok := err.(*exec.ExitError); ok {
				exitCode = exitErr.ExitCode()
				fmt.Printf("[*] clamscan exit code = %d...\n", exitCode)
			}
		}
		fmt.Println("-------- stdout")
		fmt.Println(stdout.String())
		fmt.Println("-------- stderr")
		fmt.Println(stderr.String())

		if exitCode == 0 {
			fmt.Println("[+] no viruses were identified...")
		} else if exitCode == 1 {
			fmt.Printf("[!] %s contained viruses... quarentining file\n", tmpFile)
		} else {
			fmt.Printf("[-] an error occured while running clamscan\n")
		}
	}
}

func main() {
	lambda.Start(handler)
}
