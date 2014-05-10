from scrapy.item import Item, Field

class GameItem(Item):
    url = Field()
    title = Field()
    author = Field()
    entry_type = Field()
    description = Field()
    downloads = Field()
    #screenshots = Field()
    image_urls = Field()
    images = Field()

