import folium

# 브이월드 API 키 설정
apikey = '10235D2E-E135-3D04-B51E-1052734DE2B0'

# 송도 센트럴 파크 푸르지오 아파트 중심으로 지도 초기화
map = folium.Map(
    location=[37.3945, 126.6385], 
    zoom_start=16
)

# 브이월드 배경지도 레이어 추가
folium.TileLayer(
    tiles=f'https://api.vworld.kr/req/wmts/1.0.0/{apikey}/Base/{{z}}/{{y}}/{{x}}.png',
    attr='VWorld',
    name='VWorld Base Map',
    overlay=False,
    control=True
).add_to(map)

# 지적도(LX맵) 레이어 추가
folium.WmsTileLayer(
    url='https://api.vworld.kr/req/wms?',
    layers='lt_c_landinfobasemap',
    request='GetMap',
    version='1.3.0',
    key=apikey,
    fmt='image/png',
    transparent=True,
    name='LX맵(편집지적도)',
).add_to(map)

folium.LayerControl().add_to(map)

# 결과 저장
map.save('songdo_map.html')