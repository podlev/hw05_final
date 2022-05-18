from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        help_texts = {
            'text': 'Напишите сюда текст сообщения',
            'group': 'Выберите группу или оставьте пустой',
            'image': 'Выберите картинку к посту или оставьте пустой'
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Напишите сюда текст комментария',
        }
