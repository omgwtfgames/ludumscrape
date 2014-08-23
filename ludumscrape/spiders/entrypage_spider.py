#!/usr/bin/env python
import string
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector

from ludumscrape.items import GameItem
import ludumscrape

class LudumdareSpider(CrawlSpider):

    name = 'ludumdare'
    allowed_domains = ['ludumdare.com']
    event_number = None

    def __init__(self, event_number="29", *args, **kwargs):
        if not ludumscrape.settings.ENABLE_THE_SCRAPER_I_ACTUALLY_DO_NEED_TO_USE_IT:
            print "!!!!!!!!!!!! You must enable the spider in settings.py."
            self.start_urls = []
            return
        self.event_number = event_number
        self.start_urls = ['http://www.ludumdare.com/compo/ludum-dare-%s/?action=preview&etype=' % event_number]
        self.rules = [Rule(SgmlLinkExtractor(allow=['ludum-dare-%s\/\?action=preview\&q=\&etype=\&start=\d+' 
                                                    % event_number]), follow=True),
                      Rule(SgmlLinkExtractor(allow=['ludum-dare-%s\/\?action=preview\&uid=\d+' % event_number]), 
                                                    callback='parse_entry')]
        # we need to call this last so rules get compiled correctly 
        # (alternative is to call self._compile_rules() )
        super(LudumdareSpider, self).__init__(*args, **kwargs) 
    
    def parse_entry(self, response):
        base_xpath = "//div[@class='entry']/div[@id='compo2']"
        sel = Selector(response)
        entry = GameItem()
        entry['url'] = response.url
        title_author = sel.xpath(base_xpath + "/h3/text()").extract()[0]
        # parsing title and author look more complex than they might otherwise be since
        # they need to deal with titles containing spaced hyphens, eg:
        # "Zems Online CCG - Beneath the Sea Edition! - Exeneva - "
        entry['title'] = ''.join(title_author.split(" - ")[:-2]).strip()
        entry['author'] = title_author.split(" - ")[-2].strip()
        entry['uid'] = entry['url'].split("&uid=")[1].strip()
        entry['entry_type'] = sel.xpath(base_xpath + "/h3/i/text()").extract()
        description = sel.xpath(base_xpath + "/p[@class='links']/following::p[1]/text()").extract()
        description = self.strip_whitespace(description)
        description = string.join(description, '\n')
        entry['description'] = description
        # for link text to zip together with urls: 
        download_platforms = sel.xpath(base_xpath + "/p[@class='links']/a[@href]/text()").extract()
        download_urls = sel.xpath(base_xpath + "/p[@class='links']/a/@href").extract()
        entry['downloads'] = dict(zip(download_platforms, download_urls))
        # TODO: we should capture ahref links on images here too and grab
        # any full size versions. Currently we only get the feature image and
        # the thumbnails
        entry['image_urls'] = sel.xpath(base_xpath + "/table//*/img/@src").extract()
        
        #rankings = sel.xpath(base_xpath + "/table[2]/tr/td[1]/text()").extract()
        rankings = sel.xpath(base_xpath + "/table[2]/tr/td[1]/text() | " + 
                             base_xpath + "/table[2]/tr/td[1]/img/@src").extract()
        for i, r in enumerate(rankings):
            r = r.replace("#", "")
            medals = {"gold":1, "silver":2, "bronze":3}
            for medal, rank in medals.items():
                if medal in r: 
                    r = rank
                    break
            rankings[i] = int(r)
        sections = sel.xpath(base_xpath + "/table[2]/tr/td[2]/text()").extract()
        scores = sel.xpath(base_xpath + "/table[2]/tr/td[3]/text()").extract()
        # TODO: we should normalize rating category names between compo have
        # jam (eg, "Overall" instead of "Overall(Jam)"
        entry['ratings'] = dict(zip(sections, zip(scores, rankings)))
        
        if (int(self.event_number) < 18):
            comment_author_names = sel.xpath(base_xpath + "/h4/text()").extract()
            for i, uid in enumerate(comment_author_names):
                comment_author_names[i] = uid.strip(" says ...").strip()
            
            comment_texts = sel.xpath(base_xpath + "/h4/following::p").extract()
            for i, ctext in enumerate(comment_texts):
                comment_texts[i] = ctext.replace("<br>", "\n")\
                                        .replace("<p>","")\
                                        .replace("</p>", "")\
                                        .replace("\r", "")\
                                        .strip()
            # trim of non-comment paragraphs at the end by matching the number of authors
            comment_texts = comment_texts[0:len(comment_author_names)]
            comment_dates = [None] * (len(comment_author_names) - 1)
            comment_author_uids = [None] * (len(comment_author_names) - 1)
            
        else:
            comment_author_names = sel.xpath(base_xpath + "/div[@class='comment']/div/strong/a[@href]/text()").extract()

            comment_author_uids = sel.xpath(base_xpath + "/div[@class='comment']/div/strong/a/@href").extract()
            for i, uid in enumerate(comment_author_uids):
                comment_author_uids[i] = uid.split("=")[-1:][0]

            comment_dates = sel.xpath(base_xpath + "/div[@class='comment']/div/small/text()").extract()
            comment_texts = sel.xpath(base_xpath + "/div[@class='comment']/p/text()").extract()
            comment_texts = self.strip_whitespace(comment_texts)

        entry['comments'] = zip(comment_dates, comment_author_names, comment_author_uids, comment_texts)

        return entry

    def strip_whitespace(self, str_list):
        for i, s in enumerate(str_list):
            str_list[i] = s.strip()
        return str_list

