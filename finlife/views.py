from django.shortcuts import render, get_object_or_404
from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import DepositProducts, DepositOptions
from .serializers import DepositProductsSerializer, DepositOptionsSerializer

import requests
from django.http import JsonResponse

# Create your views here.
API_KEY = settings.API_KEY

BASE_URL = 'http://finlife.fss.or.kr/finlifeapi/'

# request 모듈을 활용하여 정기예금 상품 목록 데이터를 가져와 정기예금 상품 목록과 옵션 목록 DB에 저장
@ api_view(['GET'])
def save_deposit_products(request):
    URL = BASE_URL + 'depositProductsSearch.json'
    params = {
        'auth': settings.API_KEY,
        'topFinGrpNo' : '020000',
        'pageNo' : 1,
    }
    response = requests.get(URL, params=params).json()
    deposit_products = response['result']['baseList']
    deposit_options = response['result']['optionList']
    
    # DepositProducts model에 저장
    deposit_product = DepositProducts.objects.all()
    
    if not deposit_products:
    
        for product in deposit_products:
            deposit_product = DepositProducts(
                fin_prdt_cd = product['fin_prdt_cd'],
                kor_co_nm = product['kor_co_nm'],
                fin_prdt_nm = product['fin_prdt_nm'],
                etc_note = product['etc_note'],
                join_deny = product['join_deny'],
                join_member = product['join_member'],
                join_way = product['join_way'],
                spcl_cnd = product['spcl_cnd'],
            )
            deposit_product.save()
        
        # DepositOptions model에 저장
        for option in deposit_options:
            fin_prdt_cd = DepositProducts.objects.get(fin_prdt_cd=option['fin_prdt_cd'])
            deposit_options = DepositOptions(
                fin_prdt_cd = fin_prdt_cd,
                intr_rate_type_nm = option['intr_rate_type_nm'],
                intr_rate = option['intr_rate'],
                intr_rate2 = option['intr_rate2'],
                save_trm = option['save_trm'],
            )
            deposit_options.save()

        # serializer = DepositProductsSerializer(deposit_products, many=True)
        # return Response(serializer.data)
        
    return Response({'message':'okay'})
    
    # deposit_options_serializer = DepositOptionsSerializer(deposit_options, many=True)
    # return Response({ 
    #     "deposit_products": deposit_products_serializer.data,
    #     "deposit_options": deposit_options_serializer.data,
    #     })


# GET: 전체 정기예금 상품 목록 반환, POST: 상품 데이터 저장
@ api_view(['GET', 'POST'])
def deposit_products(request):
    if request.method == 'GET':
        deposit_products = DepositProducts.objects.all()
        serializer = DepositProductsSerializer(deposit_products, many=True)
        return Response(serializer.data)
    else:
        serializer = DepositProductsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({'message': '이미 있는 데이터이거나, 데이터가 잘못 입력되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)


# 특정 상품의 옵션 리스트 반환
@ api_view(['GET'])
def deposit_product_options(request, fin_prdt_cd):
    deposit_product = get_object_or_404(DepositProducts, fin_prdt_cd=fin_prdt_cd)
    serializer = DepositOptionsSerializer(deposit_product.deposit_options.all(), many=True)
    return Response(serializer.data)


# 가입 기간에 상관없이 금리가 가장 높은 상품과 해당 상품의 옵션 리스트 출력
@ api_view(['GET'])
def top_rate(request):
    options = DepositOptions.objects.all()
    
    # 최고 우대 금리를 가진 상품 코드랑 금리 저장할 변수 초기화
    max_rate_code = ""
    max_rate = 0
    
    for option in options:
        if option.intr_rate > max_rate:
            max_rate = option.intr_rate
            max_rate_code = option.fin_prdt_cd.fin_prdt_cd
    
    # 최고 우대 금리를 가진 상품 코드로 금융 상품과 옵션 리스트 조회
    deposit_products = get_object_or_404(DepositProducts, fin_prdt_cd=max_rate_code)
    deposit_options = DepositOptions.objects.filter(fin_prdt_cd=max_rate_code)
    
    # 시리얼라이즈하기
    product_serilizer = DepositProductsSerializer(deposit_products)
    option_serilizer = DepositOptionsSerializer(deposit_options, many=True)
    
    response = {
        'products': product_serilizer.data,
        'options': option_serilizer.data
    }
    
    return Response(response)