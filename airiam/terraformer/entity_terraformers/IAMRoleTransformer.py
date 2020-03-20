from airiam.terraformer.entity_terraformers.BaseEntityTransformer import BaseEntityTransformer, Principal
from airiam.terraformer.entity_terraformers.IAMManagedPolicyAttachmentTransformer import IAMManagedPolicyAttachmentTransformer
from airiam.terraformer.entity_terraformers.IAMInlinePolicyTransformer import IAMInlinePolicyTransformer
from airiam.terraformer.entity_terraformers.IAMPolicyDocumentTransformer import IAMPolicyDocumentTransformer
from airiam.terraformer.entity_terraformers.InstancProfileTransformer import InstanceProfileTransformer


class IAMRoleTransformer(BaseEntityTransformer):
    def __init__(self, entity_json: dict):
        self._sub_entities_to_import = []
        super().__init__('aws_iam_role', BaseEntityTransformer.safe_name_converter(entity_json['RoleName']), entity_json)

    def _generate_hcl2_code(self, entity_json) -> str:
        description_field = f"  description = \"{entity_json['Description']}\"\n"
        assume_policy_document = IAMPolicyDocumentTransformer(entity_json['AssumeRolePolicyDocument'], f"{self._safe_name}_assume_role_policy")
        role_policies = ""
        for role_policy in entity_json['RolePolicyList']:
            transformer = IAMInlinePolicyTransformer(role_policy, self._safe_name, Principal.Role)
            role_policies += transformer.code()
            self._sub_entities_to_import += transformer.entities_to_import()
        for policy_attachment in entity_json['AttachedManagedPolicies']:
            transformer = IAMManagedPolicyAttachmentTransformer(policy_attachment, self._safe_name, Principal.Role)
            role_policies += transformer.code()
            self._sub_entities_to_import += transformer.entities_to_import()
        instance_profiles = ""
        for instance_profile in entity_json['InstanceProfileList']:
            transformer = InstanceProfileTransformer(instance_profile, self.identifier())
            instance_profiles += transformer.code()
            self._sub_entities_to_import += transformer.entities_to_import()

        # TODO: Add default tags to all entities
        tags = ''
        if len(entity_json.get('Tags', [])) > 0:
            tags = self.transform_tags(entity_json)

        return f"""resource "aws_iam_role" "{self._safe_name}" {{
  name = "{entity_json['RoleName']}"
  path = "{entity_json['Path']}"
  # force_detach_policies = true
  {description_field}assume_role_policy = {assume_policy_document.identifier()}.json
  {tags}
}}

{assume_policy_document.code()}

{role_policies}
{instance_profiles}"""

    def entities_to_import(self) -> list:
        return super().entities_to_import() + self._sub_entities_to_import
