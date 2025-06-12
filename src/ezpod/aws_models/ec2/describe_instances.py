from __future__ import annotations

import subprocess

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Self

# ────────────────────────────────
# Low‑level leaf structures
# ────────────────────────────────


class Operator(BaseModel):
    managed: Optional[bool] = Field(None, alias="Managed")
    principal: Optional[str] = Field(None, alias="Principal")


class Tag(BaseModel):
    key: Optional[str] = Field(None, alias="Key")
    value: Optional[str] = Field(None, alias="Value")


class ProductCode(BaseModel):
    product_code_id: Optional[str] = Field(None, alias="ProductCodeId")
    product_code_type: Optional[str] = Field(None, alias="ProductCodeType")


class GroupIdentifier(BaseModel):
    group_id: Optional[str] = Field(None, alias="GroupId")
    group_name: Optional[str] = Field(None, alias="GroupName")


# ────────────────────────────────
# Block‑device hierarchy
# ────────────────────────────────


class Ebs(BaseModel):
    attach_time: Optional[datetime] = Field(None, alias="AttachTime")
    delete_on_termination: Optional[bool] = Field(None, alias="DeleteOnTermination")
    status: Optional[str] = Field(None, alias="Status")
    volume_id: Optional[str] = Field(None, alias="VolumeId")
    associated_resource: Optional[str] = Field(None, alias="AssociatedResource")
    volume_owner_id: Optional[str] = Field(None, alias="VolumeOwnerId")
    operator: Optional[Operator] = Field(None, alias="Operator")


class BlockDeviceMapping(BaseModel):
    device_name: Optional[str] = Field(None, alias="DeviceName")
    ebs: Optional[Ebs] = Field(None, alias="Ebs")


# ────────────────────────────────
# IAM and metadata
# ────────────────────────────────


class IamInstanceProfile(BaseModel):
    arn: Optional[str] = Field(None, alias="Arn")
    id: Optional[str] = Field(None, alias="Id")


class MetadataOptions(BaseModel):
    state: Optional[str] = Field(None, alias="State")
    http_tokens: Optional[str] = Field(None, alias="HttpTokens")
    http_put_response_hop_limit: Optional[int] = Field(
        None, alias="HttpPutResponseHopLimit"
    )
    http_endpoint: Optional[str] = Field(None, alias="HttpEndpoint")
    http_protocol_ipv6: Optional[str] = Field(None, alias="HttpProtocolIpv6")
    instance_metadata_tags: Optional[str] = Field(None, alias="InstanceMetadataTags")


# ────────────────────────────────
# Networking hierarchy
# ────────────────────────────────


class EnaSrdUdpSpecification(BaseModel):
    ena_srd_udp_enabled: Optional[bool] = Field(None, alias="EnaSrdUdpEnabled")


class EnaSrdSpecification(BaseModel):
    ena_srd_enabled: Optional[bool] = Field(None, alias="EnaSrdEnabled")
    ena_srd_udp_specification: Optional[EnaSrdUdpSpecification] = Field(
        None, alias="EnaSrdUdpSpecification"
    )


class NetworkInterfaceAttachment(BaseModel):
    attach_time: Optional[datetime] = Field(None, alias="AttachTime")
    attachment_id: Optional[str] = Field(None, alias="AttachmentId")
    delete_on_termination: Optional[bool] = Field(None, alias="DeleteOnTermination")
    device_index: Optional[int] = Field(None, alias="DeviceIndex")
    status: Optional[str] = Field(None, alias="Status")
    network_card_index: Optional[int] = Field(None, alias="NetworkCardIndex")
    ena_srd_specification: Optional[EnaSrdSpecification] = Field(
        None, alias="EnaSrdSpecification"
    )


class Ipv6Address(BaseModel):
    ipv6_address: Optional[str] = Field(None, alias="Ipv6Address")
    is_primary_ipv6: Optional[bool] = Field(None, alias="IsPrimaryIpv6")


class PrivateIpAssociation(BaseModel):
    carrier_ip: Optional[str] = Field(None, alias="CarrierIp")
    customer_owned_ip: Optional[str] = Field(None, alias="CustomerOwnedIp")
    ip_owner_id: Optional[str] = Field(None, alias="IpOwnerId")
    public_dns_name: Optional[str] = Field(None, alias="PublicDnsName")
    public_ip: Optional[str] = Field(None, alias="PublicIp")


class PrivateIpAddress(BaseModel):
    association: Optional[PrivateIpAssociation] = Field(None, alias="Association")
    primary: Optional[bool] = Field(None, alias="Primary")
    private_dns_name: Optional[str] = Field(None, alias="PrivateDnsName")
    private_ip_address: Optional[str] = Field(None, alias="PrivateIpAddress")


class Ipv4Prefix(BaseModel):
    ipv4_prefix: Optional[str] = Field(None, alias="Ipv4Prefix")


class Ipv6Prefix(BaseModel):
    ipv6_prefix: Optional[str] = Field(None, alias="Ipv6Prefix")


class ConnectionTrackingConfiguration(BaseModel):
    tcp_established_timeout: Optional[int] = Field(None, alias="TcpEstablishedTimeout")
    udp_stream_timeout: Optional[int] = Field(None, alias="UdpStreamTimeout")
    udp_timeout: Optional[int] = Field(None, alias="UdpTimeout")


class NetworkInterface(BaseModel):
    association: Optional[PrivateIpAssociation] = Field(None, alias="Association")
    attachment: Optional[NetworkInterfaceAttachment] = Field(None, alias="Attachment")
    description: Optional[str] = Field(None, alias="Description")
    groups: Optional[List[GroupIdentifier]] = Field(None, alias="Groups")
    ipv6_addresses: Optional[List[Ipv6Address]] = Field(None, alias="Ipv6Addresses")
    mac_address: Optional[str] = Field(None, alias="MacAddress")
    network_interface_id: Optional[str] = Field(None, alias="NetworkInterfaceId")
    owner_id: Optional[str] = Field(None, alias="OwnerId")
    private_dns_name: Optional[str] = Field(None, alias="PrivateDnsName")
    private_ip_address: Optional[str] = Field(None, alias="PrivateIpAddress")
    private_ip_addresses: Optional[List[PrivateIpAddress]] = Field(
        None, alias="PrivateIpAddresses"
    )
    source_dest_check: Optional[bool] = Field(None, alias="SourceDestCheck")
    status: Optional[str] = Field(None, alias="Status")
    subnet_id: Optional[str] = Field(None, alias="SubnetId")
    vpc_id: Optional[str] = Field(None, alias="VpcId")
    interface_type: Optional[str] = Field(None, alias="InterfaceType")
    ipv4_prefixes: Optional[List[Ipv4Prefix]] = Field(None, alias="Ipv4Prefixes")
    ipv6_prefixes: Optional[List[Ipv6Prefix]] = Field(None, alias="Ipv6Prefixes")
    connection_tracking_configuration: Optional[ConnectionTrackingConfiguration] = (
        Field(None, alias="ConnectionTrackingConfiguration")
    )
    operator: Optional[Operator] = Field(None, alias="Operator")


# ────────────────────────────────
# Instance‑level structures
# ────────────────────────────────


class StateReason(BaseModel):
    code: Optional[str] = Field(None, alias="Code")
    message: Optional[str] = Field(None, alias="Message")


class CpuOptions(BaseModel):
    core_count: Optional[int] = Field(None, alias="CoreCount")
    threads_per_core: Optional[int] = Field(None, alias="ThreadsPerCore")
    amd_sev_snp: Optional[str] = Field(None, alias="AmdSevSnp")


class Placement(BaseModel):
    affinity: Optional[str] = Field(None, alias="Affinity")
    group_name: Optional[str] = Field(None, alias="GroupName")
    partition_number: Optional[int] = Field(None, alias="PartitionNumber")
    host_id: Optional[str] = Field(None, alias="HostId")
    tenancy: Optional[str] = Field(None, alias="Tenancy")
    spread_domain: Optional[str] = Field(None, alias="SpreadDomain")
    host_resource_group_arn: Optional[str] = Field(None, alias="HostResourceGroupArn")
    group_id: Optional[str] = Field(None, alias="GroupId")
    availability_zone: Optional[str] = Field(None, alias="AvailabilityZone")


class InstanceState(BaseModel):
    code: Optional[int] = Field(None, alias="Code")
    name: Optional[str] = Field(None, alias="Name")


class Instance(BaseModel):
    instance_id: Optional[str] = Field(None, alias="InstanceId")
    image_id: Optional[str] = Field(None, alias="ImageId")
    instance_type: Optional[str] = Field(None, alias="InstanceType")
    launch_time: Optional[datetime] = Field(None, alias="LaunchTime")

    architecture: Optional[str] = Field(None, alias="Architecture")
    block_device_mappings: Optional[List[BlockDeviceMapping]] = Field(
        None, alias="BlockDeviceMappings"
    )

    client_token: Optional[str] = Field(None, alias="ClientToken")
    ebs_optimized: Optional[bool] = Field(None, alias="EbsOptimized")
    ena_support: Optional[bool] = Field(None, alias="EnaSupport")
    hypervisor: Optional[str] = Field(None, alias="Hypervisor")

    iam_instance_profile: Optional[IamInstanceProfile] = Field(
        None, alias="IamInstanceProfile"
    )

    network_interfaces: Optional[List[NetworkInterface]] = Field(
        None, alias="NetworkInterfaces"
    )

    outpost_arn: Optional[str] = Field(None, alias="OutpostArn")
    root_device_name: Optional[str] = Field(None, alias="RootDeviceName")
    root_device_type: Optional[str] = Field(None, alias="RootDeviceType")

    security_groups: Optional[List[GroupIdentifier]] = Field(
        None, alias="SecurityGroups"
    )

    source_dest_check: Optional[bool] = Field(None, alias="SourceDestCheck")

    state_reason: Optional[StateReason] = Field(None, alias="StateReason")
    state: Optional[InstanceState] = Field(None, alias="State")

    tags: Optional[List[Tag]] = Field(None, alias="Tags")
    virtualization_type: Optional[str] = Field(None, alias="VirtualizationType")
    cpu_options: Optional[CpuOptions] = Field(None, alias="CpuOptions")
    placement: Optional[Placement] = Field(None, alias="Placement")

    # … dozens more fields exist; add them here if you need them.
    # Pydantic will happily ignore extra keys you haven’t modeled
    # when you set `model_config = ConfigDict(extra="ignore")`.

    class Config:
        extra = "ignore"  # let unknown fields pass straight through
        populate_by_name = True  # allow either alias or pythonic field names


# ────────────────────────────────
# Reservation & top‑level wrapper
# ────────────────────────────────


class Reservation(BaseModel):
    reservation_id: Optional[str] = Field(None, alias="ReservationId")
    owner_id: Optional[str] = Field(None, alias="OwnerId")
    requester_id: Optional[str] = Field(None, alias="RequesterId")

    groups: Optional[List[GroupIdentifier]] = Field(None, alias="Groups")
    instances: Optional[List[Instance]] = Field(None, alias="Instances")


class DescribeInstancesResponse(BaseModel):
    next_token: Optional[str] = Field(None, alias="NextToken")
    reservations: Optional[List[Reservation]] = Field(None, alias="Reservations")

    @classmethod
    def get(cls) -> Self:
        cmd = "aws ec2 describe-instances --output json"
        output = subprocess.check_output(cmd, shell=True)
        inst = cls.model_validate_json(output)
        return [i for r in inst.Reservations for i in r.Instances]


# ────────────────────────────────
# Resolve forward references
# ────────────────────────────────
DescribeInstancesResponse.model_rebuild()
