import os
import subprocess
from typing import ClassVar

from pydantic import BaseModel
from typing_extensions import Self

from ezpod.BasePodCreationConfig import BasePodCreationConfig, boto3


class EbsBlockDevice(BaseModel):
    DeleteOnTermination: bool | None = True
    VolumeSize: int | None = 100
    VolumeType: str | None = "gp3"
    Iops: int | None = None
    SnapshotId: str | None = None
    Throughput: int | None = None


class AWSBlockDeviceMapping(BaseModel):
    DeviceName: str | None = "/dev/sda1"
    Ebs: EbsBlockDevice | None = None
    VirtualName: str | None = None


class AWSPodCreationConfig(BasePodCreationConfig):
    """Configuration for launching an AWS EC2 instance.

    The defaults can be overridden via environment variables so that the same
    workflow that currently exists for RunPod keeps working for AWS with just
    environment tweaks.
    """

    config_ext: ClassVar[str] = "ec2.json"
    # General EC2 parameters
    region: str | None = os.environ.get("EZPOD_AWS_REGION", "us-west-2")
    ami_id: str = os.environ.get(
        "EZPOD_AWS_AMI", "ami-0293abf1eb6f402c6"
    )  # Ubuntu 22.04 LTS (example)
    instance_type: str = os.environ.get("EZPOD_AWS_TYPE", "t2.micro")
    key_name: str = os.environ.get("EZPOD_AWS_KEY_NAME", "testkey2")
    security_group_ids: list[str] = [
        sg.strip()
        for sg in os.environ.get("EZPOD_AWS_SG_IDS", "sg-07df4d19ad1b1bf8f").split(",")
        if sg.strip()
    ]
    subnet_id: str | None = os.environ.get("EZPOD_AWS_SUBNET_ID", None)
    volume_size: int = int(os.environ.get("EZPOD_AWS_VOLUME_SIZE", 100))  # GiB
    iam_instance_profile: str | None = os.environ.get("EZPOD_AWS_IAM_PROFILE", None)

    def _client(self):
        if boto3 is None:
            raise ImportError(
                "boto3 is required for AWS support. Please `pip install boto3` or add it to requirements.txt."
            )
        return boto3.client("ec2", region_name=self.region)

    def _create_impl(self, name: str):  # type: ignore[override]
        """Create an EC2 instance and tag it so that ezpod can identify it later."""

        ec2 = self._client()
        block_device_mappings = AWSBlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=EbsBlockDevice(
                DeleteOnTermination=True,
                VolumeSize=self.volume_size,
                VolumeType="gp3",
            ),
        )
        # block_device_mappings = [
        #     {
        #         "DeviceName": "/dev/sda1",
        #         "Ebs": {
        #             "DeleteOnTermination": True,
        #             "VolumeSize": self.volume_size,
        #             "VolumeType": "gp3",
        #         },
        #     }
        # ]

        # launch_spec = {
        #     "ImageId": self.ami_id,
        #     "InstanceType": self.instance_type,
        #     "KeyName": self.key_name,
        #     "BlockDeviceMappings": block_device_mappings,
        #     "TagSpecifications": [
        #         {
        #             "ResourceType": "instance",
        #             "Tags": [
        #                 {"Key": "Name", "Value": name},
        #                 {"Key": "EzPod", "Value": "true"},
        #             ],
        #         }
        #     ],
        #     "MinCount": 1,
        #     "MaxCount": 1,
        # }

        # if self.security_group_ids:
        #     launch_spec["SecurityGroupIds"] = self.security_group_ids  # type: ignore[arg-type]
        # if self.subnet_id is not None:
        #     launch_spec["SubnetId"] = self.subnet_id  # type: ignore[arg-type]

        # if self.iam_instance_profile is not None:
        #     launch_spec["IamInstanceProfile"] = {"Name": self.iam_instance_profile}

        # # Perform the actual launch
        # response = ec2.run_instances(**launch_spec)

        # instance_id = response["Instances"][0]["InstanceId"]
        # print(f"Created instance {instance_id}")
        # return instance_id

        region_arg = f"--region {self.region}" if self.region else ""
        subnet_arg = f"--subnet-id {self.subnet_id}" if self.subnet_id else ""

        cmd = f"""aws ec2 run-instances \
    --image-id {self.ami_id} \
    --instance-type {self.instance_type} \
    --key-name {self.key_name} \
    --security-group-ids {','.join(self.security_group_ids)} \
    --count 1 \
    --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value={name}}}]' \
    {subnet_arg} \
    {region_arg} \
    --block-device-mappings '{str(block_device_mappings.model_dump_json(exclude_none=True)).replace("'", '"')}'
    """
        print(cmd)
        r = subprocess.run(cmd, shell=True)
        # print(r.stdout.decode("utf-8"))
        if r.stderr:
            raise Exception(r.stderr.decode("utf-8"))
        return r

    @classmethod
    def interactive_make(cls) -> Self:
        default = cls()
        region = input(f"Region (default: {default.region}): ") or default.region
        ami_id = input(f"AMI ID (default: {default.ami_id}): ") or default.ami_id
        instance_type = (
            input(f"Instance type (default: {default.instance_type}): ")
            or default.instance_type
        )
        key_name = (
            input(f"Key name (default: {default.key_name}): ") or default.key_name
        )
        security_group_ids = (
            input(f"Security group IDs (default: {default.security_group_ids}): ")
            or default.security_group_ids
        )
        subnet_id = (
            input(f"Subnet ID (default: {default.subnet_id}): ") or default.subnet_id
        )
        volume_size = (
            input(f"Volume size (default: {default.volume_size}): ")
            or default.volume_size
        )
        iam_instance_profile = (
            input(f"IAM instance profile (default: {default.iam_instance_profile}): ")
            or default.iam_instance_profile
        )

        return cls(
            region=region,
            ami_id=ami_id,
            instance_type=instance_type,
            key_name=key_name,
            security_group_ids=security_group_ids,
            subnet_id=subnet_id,
            volume_size=volume_size,
            iam_instance_profile=iam_instance_profile,
        )
