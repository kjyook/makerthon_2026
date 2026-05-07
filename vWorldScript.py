import folium

map = folium.Map(
    location=[37.3945, 126.6385], 
    zoom_start=16
)

map.save('templates/vWorldBase.html')

# 브이월드 배경지도
apikey = '10235D2E-E135-3D04-B51E-1052734DE2B0' # 브이월드 오픈API

folium.TileLayer(
    tiles=f'https://api.vworld.kr/req/wmts/1.0.0/{apikey}/Base/{{z}}/{{y}}/{{x}}.png',
    attr='VWorld',
    name='VWorld Base Map',
    overlay=False,
    control=True
).add_to(map)

# 주제도 가시화
folium.WmsTileLayer(
    url = 'https://api.vworld.kr/req/wms?',
    layers = 'lt_c_landinfobasemap',
    request = 'GetMap',
    version='1.3.0',
    height=256,
    width=256,
    key=apikey,
    fmt='image/png',
    transparent=True, # 주제도 투명도
    name='LX맵(편집지적도)',
).add_to(map)

folium.LayerControl().add_to(map)

map.save('templates/lxMap.html')