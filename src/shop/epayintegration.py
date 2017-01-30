### epay callback function
@require_safe
def api_epay_callback(request):
    ### save GET payload
    callback = EpayCallback.objects.create(
        json_payload=json.dumps(request.GET),
        callback_time=timezone.now(),
    )

    ### find order
    if 'orderid' in request.GET:
        ### find order type
        if request.GET['orderid'][0] == "M":
            ### find epay order
            try:
                order = EpayOrder.objects.get(id=request.GET['orderid'][1:])
            except EpayOrder.DoesNotExist:
                print "epay callback - epayorder %s not found" % request.GET['orderid']
                return HttpResponse("Not OK")

            ### check hash here
            if 'hash' not in request.GET:
                print "epay callback - missing epay hash"
                return HttpResponse("Not OK")

            ### this does not work sometimes, ordering is off maybe?
            hashstring = ''
            qs = request.META['QUERY_STRING']
            print "querystring is %s" % qs
            for kv in qs.split("&"):
                print "hashstring is now %s" % hashstring
                if kv.split("=")[0] != "hash":
                    hashstring += kv.split("=")[1]
            print "hashstring is now %s" % hashstring
            hashstring += settings.EPAY_MD5_SECRET
            epayhash = hashlib.md5(hashstring).hexdigest()
            if epayhash != request.GET['hash']:
                print "epay callback - wrong epay hash"
                return HttpResponse("Not OK")

            ### save callback in epayorder
            order.epay_callback = callback
            if 'txnid' in request.GET:
                order.epay_txnid=request.GET['txnid']
            if 'amount' in request.GET:
                order.epay_amount=int(request.GET['amount'])/100
            if 'fraud' in request.GET:
                if request.GET['fraud'] == '1':
                    order.epay_fraud=True
                else:
                    order.epay_fraud=False

            ### delay epayorder depending on user level
            if settings.ACCOUNT_LEVEL_SETTINGS[str(order.user.profile.account_level)]['MOBILEPAY_DELAY_DAYS'] > 0:
                order.btc_processing_delayed = True

            ### all ok?
            if order.epay_amount == order.xxx_amount and not order.epay_fraud:
                order.epay_payment_ok=True

            ### save
            order.save()
        else:
            print "epay callback - order %s not recognized" % request.GET['orderid']
            return HttpResponse("Not OK")
    return HttpResponse("OK")


### epay order function
@login_required
def epay_order(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']

    country = GeoIP().country(ip)["country_code"]
    if country not in settings.PERMITTED_EPAY_COUNTRIES:
        return render(request, 'epay_sepa_only.html')

    ### get provision percent
    provision = get_provision_percent(request.user, "epayorder")

    ### convert BTC price to DKK
    btc_usd_price = CurrencyPrice.objects.get(item='BTCUSD').price
    btc_dkk_price = ConvertCurrency(btc_usd_price, 'USD', 'DKK')

    ### add provision
    btc_dkk_price_with_provision = btc_dkk_price * provision

    ### instantiate form
    form = EpayOrderForm(request.POST or None, request=request, initial={
        'currency': request.user.profile.preferred_currency,
        'btc_address': request.user.profile.btc_address,
    })

    if form.is_valid():
        ### Check exhange rates
        check_if_exchange_rates_are_too_old()

        ### save order
        try:
            ### save epay order with commit=False
            epayorder = form.save(commit=False)
        except Exception as E:
            print "unable to save epay order with commit=false"
            return render(request, 'epay_order_fail.html', {
                'message': _('Unable to save epay order. Please try again, and please contact us if the problem persists.')
            })

        ### set useragent and IP
        epayorder.useragent = request.META['HTTP_USER_AGENT']
        epayorder.ip = ip

        ### create time
        epayorder.create_time = timezone.now()

        ### set order user
        epayorder.user = request.user

        ### save DKK amount
        epayorder.dkk_amount = ConvertCurrency(epayorder.xxx_amount, epayorder.currency, 'DKK')

        ### set fee
        epayorder.fee = settings.ACCOUNT_LEVEL_SETTINGS[str(epayorder.user.profile.account_level)]['MOBILEPAY_PROVISION']

        ### save epayorder
        epayorder.save()

        ### save btc_address to profile if needed
        if not request.user.profile.btc_address:
            request.user.profile.btc_address = epayorder.btc_address
            request.user.profile.save()

        send_amqp_message("epayorder M%s created by user %s" % (epayorder.id, request.user), "epayorder.create")
        return HttpResponseRedirect(reverse('epay_epay_form', kwargs={'epayorderid': epayorder.id}))

    ### calculate BTC price for the users native currency
    btc_xxx_price = ConvertCurrency(amount=btc_usd_price, fromcurrency="USD", tocurrency=request.user.profile.preferred_currency or "EUR")

    ### add provision
    btc_xxx_price = btc_xxx_price * provision

    ### find out if new orders by this user should be delayed
    if settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level)]['MOBILEPAY_DELAY_DAYS'] == 0:
        skipdelay = True
    else:
        skipdelay = False

    ### delay relevant?
    if settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level)]['MOBILEPAY_DELAY_DAYS'] > 0:
        nextlevel_history_delay = settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level+1)]['BUY_HISTORY_DELAY_DAYS']
        nextlevel_history_amount = settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level+1)]['BUY_HISTORY_MINIMUM']
    else:
        nextlevel_history_delay = None
        nextlevel_history_amount = None

    ### render the response
    return render(request, 'epay_order.html', {
        'form': form,
        'btc_xxx_price': round(btc_xxx_price, 2),
        'currency': request.user.profile.preferred_currency or "EUR",
        'provision': round((provision-1)*100, 1),
        'skipdelay': skipdelay,
        'delaydays': settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level)]['MOBILEPAY_DELAY_DAYS'],
        'daily_limit': settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level)]['MOBILEPAY_LIMIT_DAY'],
        'nextlevel_history_delay': nextlevel_history_delay,
        'nextlevel_history_amount': nextlevel_history_amount,
        'btc_address': request.user.profile.btc_address,
    })


### the page which shows the epay epay form
@login_required
def epay_epay_form(request, epayorderid):
    epayorder = get_object_or_404(EpayOrder, id=epayorderid, user=request.user, user_cancelled=False, epay_callback__isnull=True)
    accepturl = request.build_absolute_uri(reverse('epay_thanks', kwargs={'epayorderid': epayorder.id})).replace('http://', 'https://')
    description = str(request.user.id)
    hashstring = settings.EPAY_MERCHANT_NUMBER+description+'11'+str(epayorder.xxx_amount*100)+str(epayorder.currency)+'M'+str(epayorder.id)+accepturl+settings.EPAY_MD5_SECRET
    epayhash = hashlib.md5(hashstring).hexdigest()
    return render(request, 'epay_form.html', {
        'orderid': 'M%s' % epayorder.id,
        'description': description,
        'merchantnumber': settings.EPAY_MERCHANT_NUMBER,
        'amount': epayorder.xxx_amount*100,
        'currency': epayorder.currency,
        'epayhash': epayhash,
        'accepturl': accepturl,
    })


### after epay payment thanks page
@login_required
def epay_thanks(request, epayorderid):
    ### get order - if it is owned by this user and uncancelled
    epayorder = get_object_or_404(EpayOrder, id=epayorderid, user=request.user, user_cancelled=False)

    ### check for querystring
    if request.GET:
        ### update order to register thanks page view
        epayorder.thanks_page_view_time=timezone.now()
        epayorder.save()

        ### redirect to get rid of GET querystring
        return HttpResponseRedirect(reverse('epay_thanks', kwargs={'epayorderid': epayorder.id}))

    if epayorder.btc_processing_delayed:
        minamount = ConvertLimit(settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level+1)]['BUY_HISTORY_MINIMUM'], epayorder.currency)
        delaydays = settings.ACCOUNT_LEVEL_SETTINGS[str(request.user.profile.account_level)]['MOBILEPAY_DELAY_DAYS']
    else:
        minamount = None
        delaydays = None

    return render(request, 'epay_thanks.html', {
        'order': epayorder,
        'delaydays': delaydays,
        'minamount': minamount,
    })
