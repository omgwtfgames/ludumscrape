#!/usr/bin/env python

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector

from ludumscrape.items import GameItem

class LudumdareSpider(CrawlSpider):

    name = 'ludumdare'
    allowed_domains = ['ludumdare.com']
    
    def __init__(self, event_number="29", *args, **kwargs):
        self.start_urls = ['http://www.ludumdare.com/compo/ludum-dare-%s/?action=preview&etype=' % event_number]
        self.rules = [Rule(SgmlLinkExtractor(allow=['ludum-dare-%s\/\?action=preview\&q=\&etype=\&start=\d+' 
                                                    % event_number]), follow=True),
                      Rule(SgmlLinkExtractor(allow=['ludum-dare-%s\/\?action=preview\&uid=\d+']), 
                                                    callback='parse_entry')]
        # we need to call this last so rules get compiled correctly 
        # (alternative is to call self._compile_rules() )
        super(LudumdareSpider, self).__init__(*args, **kwargs) 
    
    """
    def parse_preview(self, response):
        sel = Selector(response)
        preview_page_urls = sel.xpath("//div[@class='entry']/div[@id='compo2']/p[4]/a/@href").extract()
        for url in preview_page_urls:
            yield Request(url)
    """

    def parse_entry(self, response):
        sel = Selector(response)
        entry = GameItem()
        entry['url'] = response.url
        title_author = sel.xpath("//div[@class='entry']/div[@id='compo2']/h3/text()").extract()[0]
        entry['title'] = title_author.split("-")[0].strip()
        entry['author'] = title_author.split("-")[1].strip()
        entry['entry_type'] = sel.xpath("//div[@class='entry']/div[@id='compo2']/h3/i/text()").extract()
        entry['description'] = sel.xpath("//div[@class='entry']/div[@id='compo2']/p[@class='links']/following::p[1]/text()").extract()
        # for link text to zip together with urls: 
        download_platforms = sel.xpath("//div[@class='entry']/div[@id='compo2']/p[@class='links']/a[@href]/text()").extract()
        download_urls = sel.xpath("//div[@class='entry']/div[@id='compo2']/p[@class='links']/a/@href").extract()
	entry['downloads'] = dict(zip(download_platforms, download_urls))       
        entry['image_urls'] = sel.xpath("//div[@class='entry']/div[@id='compo2']/table//*/img/@src").extract()
        return entry
