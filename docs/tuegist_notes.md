# Tuesday Gists

post one of my public gists each tuesday

- tuegist.com

## Pages

- index
- gists\...html
- about
- contact
- rss.xml

## Backend

### generator script

#### sqlite database

##### table: gists

- id
- description
- create_date
- modified_date
- published_date
- tags
- summary

#### folder structure

- src\
- src\templates\ (base.jinja, index.jinja, gist.jinja, about.jinja, contact.jinja, rss.jinja
- www\
- www\css\
- www\js\
- www\gists\


#### command-line options

- rebuild: rebuild all the pages & gists from the DB
- pages: rebuild the pages (index, about, contact, rss)
- gists: rebuild the all gists
- index: rebuild the index.html and rss.xml files
- scan: scan gists and update the DB with that info but do not build or update html files
- tues: perform the actions for the weekly post.
- log: the logfile
- out: the folder to build the output to

#### config file.

- username: the user to get the public gists for.
- logfile: the default log file
- output_folder: the default output folder
- db_file: the sqlite file that I will use to store data

#### pseudo code

- every tuesday
	- scan gists for new or updated gists.
		- load into DB leaving the published date blank.
	- pick an unpublished post (prioritizing updates over new)
	- set the pub date.
	- create the post
	- rebuild the index and rss
	- git commit the changes (this will automatically update the cloudflare pages)


### cloudflare pages


