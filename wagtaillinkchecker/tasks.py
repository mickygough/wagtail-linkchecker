from celery import shared_task
from wagtaillinkchecker.scanner import get_url, clean_url
from wagtaillinkchecker.models import ScanLink
from bs4 import BeautifulSoup
from django.db.utils import IntegrityError
from django.utils import timezone


@shared_task
def check_link(link_pk):
    link = ScanLink.objects.get(pk=link_pk)
    if isinstance(link, ScanLink):
        site = link.scan.site
        url = get_url(link.url, link.page, site)
        link.status_code = url.get('status_code')
        print(link.page.full_url)
        print(link.url)
        if url['error']:
            link.broken = True
            link.error_text = url['error_message']

        elif link.page.full_url == link.url:
            soup = BeautifulSoup(url['response'].content)
            anchors = soup.find_all('a')
            images = soup.find_all('img')

            for anchor in anchors:
                link_href = anchor.get('href')
                link_href = clean_url(link_href, site)
                if link_href:
                    try:
                        new_link = link.scan.add_link(page=link.page, url=link_href)
                        new_link.check_link()
                    except IntegrityError:
                        pass

            for image in images:
                image_src = image.get('src')
                image_src = clean_url(image_src, site)
                if image_src:
                    try:
                        new_link = link.scan.add_link(page=link.page, url=image_src)
                        new_link.check_link()
                    except IntegrityError:
                        pass
        link.crawled = True
        link.save()

        non_scanned_links = link.scan.non_scanned_links()
        print(non_scanned_links)
        if link.scan.non_scanned_links():
            pass
        else:
            scan = link.scan
            scan.scan_finished = timezone.now()
            scan.save()
    else:
        raise TypeError("Expected type 'ScanLink', received type '{0}'".format(type(link)))