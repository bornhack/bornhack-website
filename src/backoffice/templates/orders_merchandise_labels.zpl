{% for productrel in orderproductrelation_list %}
{% with ''|ljust:productrel.non_refunded_quantity as range %} 
{% for i in range %}
^XA
^PW600
^LL200

^FXQR Code
^FO20,20
^BQN,2,6,N,7
^FDLA,https://example.com/product/12345^FS

^FXOPR
^FO180,30
^A0N,90,90
^FD{{productrel.id}}^FS

^FXProduct name
^FO190,110
^A0N,30,30
^FD{{ productrel.product.name }}^FS

{% if productrel.non_refunded_quantity > 1 %}
^FXProduct x/z
^FO500,160
^A0N,25,25
^FD{{ forloop.counter }}/{{ productrel.non_refunded_quantity }}^FS
{% endif %}
^XZ
{% endfor %}
{% endwith %}
{% endfor %}
