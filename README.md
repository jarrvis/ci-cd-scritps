# Required Dependencies

* python2 - for branch_merger

# Usage

You need user account on bitbucket that has permissions to update settings for repositories

```
$   python branch_merger.py -u <bitbucketUsername> -p <bitbucketPassword> -k <projectKey> -r <repository> -s <sourceBranch> -d <destBranch> -t <prTitle>(optional) -m <prdDescription>(optional) 
```
