# Scrapy settings for ludumscrape project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

# You probably don't need to run this !
# There are data files from past LD scraping runs in the ./results directory.
# Save yourself the time and bandwidth, and be nice to the Ludum Dare site. 
ENABLE_THE_SCRAPER_I_ACTUALLY_DO_NEED_TO_USE_IT = False

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
