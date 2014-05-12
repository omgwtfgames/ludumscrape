# Scrapy settings for ludumscrape project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'ludumscrape'

SPIDER_MODULES = ['ludumscrape.spiders']
NEWSPIDER_MODULE = 'ludumscrape.spiders'

# we use autothrottle to be nice to the site - don't want to disrupt the humans !
AUTOTHROTTLE_ENABLED = True
#CONCURRENT_REQUESTS_PER_DOMAIN = 1
#DOWNLOAD_DELAY = 0.25

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'ludumscrape (+http://www.yourdomain.com)'

ITEM_PIPELINES = {'scrapy.contrib.pipeline.images.ImagesPipeline': 1}
IMAGES_STORE = "results/images"