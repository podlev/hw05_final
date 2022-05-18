from django.core.paginator import Paginator

POSTS_COUNT = 10


def paginator(request, post_list, count=POSTS_COUNT):
    paginator = Paginator(post_list, count)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
