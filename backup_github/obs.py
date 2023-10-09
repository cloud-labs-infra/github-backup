import logging
import sys
from obs import ObsClient, Grant, Owner, ACL, Grantee, Group, Permission


class BackupObs(ObsClient):
    def __init__(self, access_key_id,
                 secret_access_key,
                 server,
                 path_style,
                 signature,
                 is_signature_negotiation):
        super().__init__(access_key_id, secret_access_key, server, path_style, signature, is_signature_negotiation)

    def upload_backup(self, backup_name, backup_path, bucket_name):
        resp = self.putFile(bucket_name, backup_name, backup_path)
        if resp.status >= 300:
            logging.error(f'Uploading of {backup_path} failed, error message: {resp.errorMessage}')
            raise Exception(resp.errorMessage)
        logging.info(f'{backup_path} is loaded')

    def update_acl(self, backup, bucket_name):
        resp = self.getObjectAcl(bucket_name, backup)
        if resp.status >= 300:
            logging.error(f'Getting ACL of object {backup} failed, error message: {resp.errorMessage}')
            raise Exception(resp.errorMessage)
        logging.info(f'Got {backup} ACL')

        grants = list()
        if resp.body.grants:
            for grant in resp.body.grants:
                grants.append(grant)
        grants.append(Grant(grantee=Grantee(group=Group.ALL_USERS), permission=Permission.READ))
        owner = Owner(owner_id=resp.body.owner.owner_id)
        acl = ACL(owner=owner, grants=grants)

        resp = self.setObjectAcl(bucket_name, backup, acl=acl)
        if resp.status >= 300:
            logging.error(f'Setting ACL to {backup} failed, error message: {resp.errorMessage}')
            raise Exception(resp.errorMessage)
