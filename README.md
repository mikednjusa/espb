## How to Run the Benchmarks

### Requirements:
AWS User with access keys and AWS CLI set up already

### Usage:
python run-benchmarking.py –config-file <config-file> --data-file <JSON data file>

The script will take in a config file and set up the benchmarking cluster and monitoring. It will use the data file to run the esrally benchmarking test. After the benchmarking is done, it will save the data to an S3 bucket and then tear itself down. 

### Config File:

The script will take in a config file with the following parameters:

NUM_OF_INSTANCES -number of benchmarking instances, max 5

INSTANCE_TYPE -i.e. m4.large

DEDICATED_HOST_ID -if a host id is provided then it will use the dedicated host instead of regular instances

DEDICATED_HOST_INSTANCE_TYPE -i.e. m4.large

NUM_DEDICATED_HOST_INSTANCES -number of benchmarking instances launched on dedicated hosts, max 5

INSTANCE_KEY_PAIR -their desired instance key pair in case they want to be able to access the instances. Otherwise if left blank the script will create an instance key pair. 

S3_BUCKET -the location of the S3 bucket where JSON data will be stored. 

LOCAL_DATA_DIR: Optional local drive to save the JSON data
 
### Data File:

Example: 
{
 
  "test_suites": {
 
    "testsuite_001": [
 
      {
 
        "name": "large_track_tiny1",
 
        "instance_type": "m3.medium",
 
        "security_group_ids": "",
 
        "region": "us-west-2",
 
        "test": "esrally --pipeline=from-distribution --distribution-version=5.0.0 --track=geonames --test-mode",
 
        "rally_config": "conditional_install_items/rally_csv.ini",
 
        "root_size_gb": 16,
 
        "do_run": false,
 
        "save_on_failure": false
 
      }
}
 
The user will be able to add their own rally.ini files in the rally_config parameter:

## Formatting Hints 

Welcome to GitHub Pages

You can use the [editor on GitHub](https://github.com/mikednjusa/espb/edit/master/README.md) to maintain and preview the content for your website in Markdown files.

Whenever you commit to this repository, GitHub Pages will run [Jekyll](https://jekyllrb.com/) to rebuild the pages in your site, from the content in your Markdown files.

### Markdown

Markdown is a lightweight and easy-to-use syntax for styling your writing. It includes conventions for

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```

For more details see [GitHub Flavored Markdown](https://guides.github.com/features/mastering-markdown/).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/mikednjusa/espb/settings). The name of this theme is saved in the Jekyll `_config.yml` configuration file.

### Support or Contact

Having trouble with Pages? Check out our [documentation](https://help.github.com/categories/github-pages-basics/) or [contact support](https://github.com/contact) and we’ll help you sort it out.
