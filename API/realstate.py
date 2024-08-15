import logging
import requests
import xml.etree.ElementTree as ET
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from apibase import APIBase  # APIBase 클래스를 import

logger = logging.getLogger(__name__)

class RealEstateAPI(APIBase):
    def __init__(self, api_key, llm_api_key):
        super().__init__(llm_api_key)
        self.api_key = api_key

    def get_lawd_cd(self, region_name):
        # 'bjdData.txt'에서 지역명을 기반으로 법정동 코드를 찾아 반환하는 함수
        with open('config/bjdData.txt', 'r', encoding='cp949') as file:
            for line in file:
                simplified_line = ' '.join(line.split('\t')[1:]).strip().replace(" ", "")
                if region_name.replace(" ", "") in simplified_line:
                    return line.split('\t')[0][:5]  # 법정동 코드의 처음 5자리 반환
        return None
    
    def estimate_supply_area(self, exclu_use_ar):
        # 전용면적을 바탕으로 공급면적을 추정 (일반적으로 20%~40%를 더하는 방식)
        estimated_supply_area = exclu_use_ar * 1.3  # 1.3은 전용면적 대비 공급면적의 추정 비율
        return round(estimated_supply_area, 2)  # 소수점 2자리까지 반올림하여 반환


    def calculate_pyeong(self, supply_area):
        # 공급면적을 바탕으로 평수 계산 (1평 = 3.3㎡)
        pyeong = supply_area / 3.3
        return round(pyeong, 2)  # 평수를 소수점 둘째 자리에서 반올림


    def get_real_estate_data(self, lawd_cd, deal_ymd, num_of_rows=100, page_no=1):
        self.logger.info(f'Fetching real estate data for LAWD_CD: {lawd_cd}, DEAL_YMD: {deal_ymd}')
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
        params = {
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ymd,
            "serviceKey": self.api_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            self.logger.error(f"Failed to fetch data: {response.status_code}")
            return []
        
        xml_data = response.content
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall('.//item'):
            apt_nm = item.find('aptNm').text if item.find('aptNm') is not None else "정보 없음"
            umdNm = item.find('umdNm').text if item.find('umdNm') is not None else "정보 없음"
            exclu_use_ar = item.find('excluUseAr').text if item.find('excluUseAr') is not None else "정보 없음"
            deal_amount = item.find('dealAmount').text if item.find('dealAmount') is not None else "정보 없음"
            floor = item.find('floor').text if item.find('floor') is not None else "정보 없음"
            deal_year = item.find('dealYear').text if item.find('dealYear') is not None else "정보 없음"
            deal_month = item.find('dealMonth').text if item.find('dealMonth') is not None else "정보 없음"
            deal_day = item.find('dealDay').text if item.find('dealDay') is not None else "정보 없음"
            date = f"{deal_year}-{deal_month}-{deal_day}"

            items.append({
                'aptNm': apt_nm,
                'umdNm': umdNm,
                'excluUseAr': exclu_use_ar,
                'dealAmount': deal_amount,
                'floor': floor,
                'date': date
            })
        
        self.logger.info(f'Fetched {len(items)} real estate items')
        return items

    async def send_real_estate_summaries(self, update, context):
        if "세종특별자치시" in context.args[1]:
            if len(context.args) < 3:
                await update.message.reply_text('올바른 형식으로 입력해 주세요: /realstate DEAL_YMD CITY DONG')
                return
            deal_ymd = context.args[0]
            city = context.args[1]
            dong = context.args[2]  # 동 이름을 추가로 입력받습니다.
            region_name = f"{city} {dong}"
            filter_by_dong = True
        else:
            if len(context.args) < 3:
                await update.message.reply_text('올바른 형식으로 입력해 주세요: /realstate DEAL_YMD CITY DISTRICT [DONG]')
                return
            deal_ymd = context.args[0]
            city = context.args[1]
            district = context.args[2]
            dong = context.args[3] if len(context.args) > 3 else None  # 동 이름이 없을 경우 None으로 설정
            region_name = f"{city} {district}"
            filter_by_dong = dong is not None

        lawd_cd = self.get_lawd_cd(region_name)
        if not lawd_cd:
            await update.message.reply_text(f'해당 지역의 법정동 코드를 찾을 수 없습니다: {region_name}')
            return
        
        items = self.get_real_estate_data(lawd_cd, deal_ymd)
        
        if not items:
            await update.message.reply_text('해당 날짜에 데이터가 없습니다.')
            return

        # umdNm 값들을 로그에 출력하여 확인
        self.logger.info(f'조회된 데이터의 법정동 이름들: {[item["umdNm"] for item in items]}')

        if filter_by_dong:
            # 사용자가 입력한 동 이름으로 필터링 (대소문자 및 공백 무시)
            filtered_items = [
                item for item in items 
                if dong.replace(" ", "").lower() in item['umdNm'].replace(" ", "").lower()
            ]
        else:
            # 동 이름 없이 모든 데이터를 선택
            filtered_items = items

        self.logger.info(f'필터링된 데이터: {filtered_items}')

        if not filtered_items:
            await update.message.reply_text(f'{dong} 관련 데이터가 없습니다.' if filter_by_dong else '해당 시/군 관련 데이터가 없습니다.')
            return

        # 필터링된 데이터 중 최대 10개만 선택
        selected_items = filtered_items[:10]

        summaries = []
        for item in selected_items:
            # 전용면적을 소수점 2자리로 통일
            exclu_use_ar = round(float(item['excluUseAr']), 2)
            estimated_supply_area = self.estimate_supply_area(exclu_use_ar)
            pyeong = self.calculate_pyeong(estimated_supply_area)

            # 출력 형식에서 소수점 자릿수를 통일하여 표시
            context_text = (
                f"법정동: {item['umdNm']}\n"
                f"아파트: {item['aptNm']}\n"
                f"전용면적: {exclu_use_ar:.2f}㎡\n"
                f"추정 공급면적: {estimated_supply_area:.2f}㎡\n"
                f"평수(추정): {pyeong:.2f}평\n"
                f"거래금액: {item['dealAmount']}만원\n"
                f"층: {item['floor']}층\n"
                f"거래일자: {item['date']}"
            )
            question = "요약해줘"
            try:
                result = self.chain_with_context.invoke({"context": context_text, "question": question})
                summaries.append(result)
                self.logger.info('Generated summary for a real estate item')
            except Exception as e:
                self.logger.error(f'Error generating summary: {e}')

        for summary in summaries:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"요약:\n\n{summary}")
            self.logger.info('Sent summary to user')