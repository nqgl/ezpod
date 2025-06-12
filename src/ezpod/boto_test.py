# %%
import boto3

ec2 = boto3.resource("ec2")
from ezpod.ec2_data import EC2Data

ecd = EC2Data.get_all_pods()
inst = ec2.Instance(ecd[0].id)

# %%
help(ec2)
# %%
dir(ec2)
# %

for i in ec2.instances.all():
    print(i.id)
# %%
print(dir(i))
# %%
i.id
# %%
i.instance_id
# %%
i.state
# %%
i.reboot()
# %%
resp = {
    "ResponseMetadata": {
        "RequestId": "2cf44778-0258-4252-b94d-83673aaf12ed",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "x-amzn-requestid": "2cf44778-0258-4252-b94d-83673aaf12ed",
            "cache-control": "no-cache, no-store",
            "strict-transport-security": "max-age=31536000; includeSubDomains",
            "content-type": "text/xml;charset=UTF-8",
            "content-length": "219",
            "date": "Sun, 20 Apr 2025 23:49:06 GMT",
            "server": "AmazonEC2",
        },
        "RetryAttempts": 0,
    }
}

# %%
i.state
# %%


# %%
# %%
insts
# %%
insts.reservations[0].instances[0].state
# %%
