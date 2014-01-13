#!/usr/bin/env python

import json
import pprint

from lxml import etree
from pymongo import MongoClient
import requests
import xmltodict


class QBPInterface:

    def __init__(self):

        self.api_key = u''
        self.base_url = u'http://api.qbp.com/api/1/'

        self.headers = {
                u'X-QBPAPI-KEY': self.api_key,
                u'content-type': u'application/xhtml+xml'
                }

    def get(self, url):
        res = requests.get(url, headers=self.headers)
        return etree.fromstring(res.content)

    def post(self, url, xml_content):
        res = requests.post(url, headers=self.headers, data=xml_content)
        return etree.fromstring(res.content)

    def getSkuList(self):
        url = self.base_url + u'/product/skulist'
        xml = self.get(url)

        skus = [sku.text for sku in xml[0]]
        return skus

    def getProductsBySkuList(self, sku_list):
        url = self.base_url + u'/product/sku?stocklevels=yes'
        req_xml = self.qbpXMLRequest(u'productRequest', u'ids', u'id', sku_list)
        xml = self.post(url, etree.tostring(req_xml))

        return xml

    def qbpXMLRequest(self, parent, child, item_tag, item_list):
        xml_request = etree.Element(parent)
        id_list = etree.SubElement(xml_request, child)
        for item in item_list:
            element = etree.SubElement(id_list, item_tag)
            element.text = item

        return xml_request


qbp = QBPInterface()

client = MongoClient()
db = client.radiantretail
collection = db.product

skus = qbp.getSkuList()
for i in range(10):

    low = i*100
    high = (i+1)*100
    product_list_xml = qbp.getProductsBySkuList(skus[low:high])
    product_list_dict = xmltodict.parse(etree.tostring(product_list_xml))
    #pprint.pprint(product_list_dict['products'])
    #print json.dumps(product_list_dict['productResponse']['products']['product'], indent=2)

    collection.insert(product_list_dict['productResponse']['products']['product'])

#if __name__ == '__main__':
#    getProducts()
