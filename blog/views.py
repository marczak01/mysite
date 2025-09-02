from django.shortcuts import render, get_object_or_404, redirect
from taggit.models import Tag
from django.core.mail import send_mail
from .forms import EmailPostForm, CommentForm
# from django.http import Http404
from django.db.models import Count
from .models import Post, Comment
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST


# !!!!!!!! WIDOK OPARTY NA KLASIE !!!!!!!!
# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 2
#     template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    # stronicowanie z 3 postami na strone
    # Paginator oczekuje listy do iterowania oraz liczby elementow jaka ma wyswietlic na strone
    paginator = Paginator(post_list, 2)
    # pobieramy ze strony wartosc z page a jezeli jej nie znajdzie to daje domyslnie 1
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        #jesli zmienna page_number jest poza zasiegiem
        # wyslij ostatnia strone wynikow
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        # jesli page_number nie jest liczba zwroc pierwsza strone
        posts = paginator.page(1)
    return render(request,
                  'blog/post/list.html',
                  {'posts':posts,
                   'tag':tag})


def post_detail(request, year, month, day, post):
    # try:
    #     post = Post.published.get(id=id)
    # except Post.DoesNotExist:
    #     raise Http404("Nie znaleziono posta")
    # Mozemy uzyc get_object_or_404 zamiast powyzszego zapisu
    # tez zwroci błąd Http404
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id' ,flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form,
                   'similar_posts': similar_posts})


def post_share(request, post_id):
    # pobierz post wg id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        # formularz zostal przeslany
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # pomyślnie weryfikowano poprawność pól
            cd = form.cleaned_data
            # ...wyslij email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} zaleca Ci przeczytanie {post.title}"
            message = f"Przeczytaj {post.title} pod adresem {post_url}\n\n komentarze {cd['name']}: {cd['comments']}"
            send_mail(subject, message, 'marekmarczak25@gmail.com', [cd['to']])
            sent = True
    else:
      # else oznacza, że request.method == 'GET'
      # Strona jest ładowana po raz pierwszy i tworzony jest
      # nowy egzemplarz klasy EmailPostForm, który zostanie użyty
      # do wyświetlenia pustego formularza na stronie.
      form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post':post,
                                                    'form': form,
                                                    'sent': sent})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    
    return render(request, 'blog/post/comment.html', {'post': post,
                                                      'form': form,
                                                      'comment': comment})