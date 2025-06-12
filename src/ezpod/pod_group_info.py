from pydantic import BaseModel


class PodGroupInfo(BaseModel):
    group: str
    num: int
    bad_name_cant_parse: str | None = None

    def __str__(self):
        if self.bad_name_cant_parse is not None:
            return self.bad_name_cant_parse
        return f"{self.group}_{self.num}"

    @classmethod
    def from_str(cls, name: str):
        try:
            group, num = name.split("_")
            return cls(group=group, num=int(num))
        except:
            print("ERROR: Failed to parse bad pod name:", name)
            return cls(group="", num=0, bad_name_cant_parse=name)

    # @classmethod
    # def from_aws_tags(cls, tags: dict[str, str]):
    #     try:
    #         return cls.from_ezpod_str(tags["Name"])
    #     except:
    #         print("ERROR: Failed to parse aws tags:", tags)
    #         return cls(group="", num=0, bad_name_cant_parse=str(tags))
