import io

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.db.models.aggregates import Sum
from django.http import FileResponse


def download_shopping_cart(self, request):
    buf = io.BytesIO()
    page = canvas.Canvas(buf)
    pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
    x, y = 50, 800
    shopping_cart = (
        request.user.shopping_cart.recipe.
        values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('recipe__amount')).order_by())
    page.setFont('Vera', 14)
    if shopping_cart:
        indentation = 20
        page.drawString(x, y, 'Cписок покупок:')
        for index, recipe in enumerate(shopping_cart, start=1):
            page.drawString(
                x, y - indentation,
                f'{index}. {recipe["ingredients__name"]} - '
                f'{recipe["amount"]} '
                f'{recipe["ingredients__measurement_unit"]}.')
            y -= 15
            if y <= 50:
                page.showPage()
                y = 800
        page.save()
        buf.seek(0)
        return FileResponse(
            buf, as_attachment=True, filename='shoppinglist.pdf')
    page.setFont('Vera', 24)
    page.drawString(
        x, y, 'Cписок покупок пуст.'
    )
    page.save()
    buf.seek(0)
    return FileResponse(buf,
                        as_attachment=True,
                        filename='shoppinglist.pdf')