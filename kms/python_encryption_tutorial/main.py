from aws_encryption_sdk import (
    CommitmentPolicy,
    EncryptionSDKClient,
    StrictAwsKmsMasterKeyProvider,
)
import botocore.session


def main(key_arn):
    botocore_session = botocore.session.Session(profile="admin")

    plain_text: bytes = b"You must be shapeless, formless, like water. When you pour water in a cup, it becomes the cup. When you pour water in a bottle, it becomes the bottle. When you pour water in a teapot, it becomes the teapot. Water can drip and it can crash. Become like water my friend."

    client: EncryptionSDKClient = EncryptionSDKClient(
        commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_REQUIRE_DECRYPT,
    )

    master_key_provider = StrictAwsKmsMasterKeyProvider(
        key_ids=[key_arn],
        botocore_session=botocore_session,
    )

    cipher_text, _ = client.encrypt(
        source=plain_text,
        key_provider=master_key_provider,
    )

    cycled_text, _ = client.decrypt(
        source=cipher_text, key_provider=master_key_provider
    )

    assert cycled_text == plain_text


if __name__ == "__main__":
    from sys import argv

    if len(argv) < 2:
        print(f"usage: {argv[0]} <kms_key_arn>")
    else:
        main(key_arn=argv[1])
