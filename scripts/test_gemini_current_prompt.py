"""
현재 Gemini Detector 프롬프트로 27개 케이스 테스트
"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.llm.gemini_detector import GeminiPhishingDetector
import time

# === 전체 테스트 케이스 ===
test_cases = [
    # Category A: 전통적 보이스피싱 (1-10)
    {"id": "A01", "cat": "A", "name": "노골적 위협", "text": "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와. 안 오면 바로 수배 때린다. 폰 끄지 말고 링크 보내는 거 깔아.", "min": 90, "type": "phishing"},
    {"id": "A02", "cat": "A", "name": "어설픈 사칭", "text": "여기는 중앙지방검찰청입니다. 본인 계좌가 범죄에 연루되어 동결 예정입니다. 보안 검사를 위해 모텔 등 조용한 곳으로 이동해서 '팀뷰어' 어플을 설치하십시오.", "min": 85, "type": "phishing"},
    {"id": "A03", "cat": "A", "name": "전형적 시나리오", "text": "김철수 검사입니다. 수사 기밀 유지를 위해 제3자가 없는 독립된 공간이 필요합니다. 주변 소음이 섞이면 녹취가 증거로 채택이 안 됩니다. 근처 숙박업소로 이동하시고, 비대면 조사를 위한 보안 앱을 설치해주세요.", "min": 85, "type": "phishing"},
    {"id": "A04", "cat": "A", "name": "피해자 구제 빙자", "text": "선생님, 지금 선생님이 피의자가 아니라 피해자 입장이신 걸 소명하려는 겁니다. 다만, 녹취 중에 주변 잡음이나 타인의 목소리가 섞이면 증거 효력이 사라져요. 그래서 댁보다는 방음이 확실한 스터디룸이나 비즈니스 호텔을 권장 드리는 겁니다.", "min": 75, "type": "phishing"},
    {"id": "A05", "cat": "A", "name": "기술 지원 위장", "text": "지금 폰이 해킹된 상태라 위치 추적이 되고 있어요. 댁으로 가시면 범인들이 알 수 있습니다. 일단 공공 와이파이가 없는 안전한 장소로 피신하셔야 하고요, 해킹 차단을 위해 한국인터넷진흥원(KISA) 인증 툴을 보내드릴 테니 실행해주세요.", "min": 75, "type": "phishing"},
    {"id": "A06", "cat": "A", "name": "금감원 사칭", "text": "금융감독원 자산보호팀입니다. 현재 자금이 해외로 빠져나가고 있어 지급정지 요청을 해야 하는데, 본인 인증이 계속 실패하네요. 통신 보안이 확실한 곳에서 대기해주시면, 저희가 원격으로 '금융 보안 모듈'을 재설정해 드리겠습니다.", "min": 70, "type": "phishing"},
    {"id": "A07", "cat": "A", "name": "가족 사칭", "text": "아버님, 저 김 대리입니다. 아까 따님이 사고 합의 건으로 급하게 연락 주셨는데, 지금 상대방 보험사 직원이랑 대화 내용을 녹음해야 해요. 주변이 시끄러우면 안 되니까 조용한 방 잡고 계시면, 제가 보내드리는 '보험사 전용 녹취 앱' 켜두세요. 따님 바꿔드릴게요.", "min": 70, "type": "phishing"},
    {"id": "A08", "cat": "A", "name": "면접 위장", "text": "안녕하세요, OO기업 인사팀입니다. 1차 합격 축하드립니다. 2차는 AI 역량 검사로 진행되는데요, 부정행위 방지를 위해 독립된 공간(숙박 시설 등)에서 360도 카메라 세팅이 필요합니다. 보내드리는 '시험 감독 프로그램' 설치 후 응시 부탁드립니다.", "min": 65, "type": "phishing"},
    {"id": "A09", "cat": "A", "name": "가짜 백신", "text": "고객님, OO카드 FDS(이상거래탐지)팀입니다. 지금 고객님 폰에 악성코드가 심어져서 계속 결제 시도가 들어옵니다. 저희가 이걸 막으려면 '백신'을 업데이트해야 하는데, 데이터가 손실될 수 있으니 이동하지 마시고 한자리에서 와이파이 끄고 진행해 주세요.", "min": 65, "type": "phishing"},
    {"id": "A10", "cat": "A", "name": "생체인증 위장", "text": "네, 고객님. 불편 드려 죄송합니다. 최근 딥보이스 범죄가 늘어나서, 본인 확인 절차가 강화되었습니다. 현재 고객님 목소리의 생체 파형(Voice Print)을 등록해야 계좌 잠금이 풀리는데요, 이게 미세한 소음에도 오류가 납니다. 번거로우시겠지만, 지금 계신 카페는 소음 수치가 높아서 진행이 불가능합니다. 근처에 공유 오피스나 조용한 숙소 같은 곳을 잠시 이용해 주실 수 있을까요?", "min": 60, "type": "phishing"},

    # Category B: 정상 케이스 (11-13)
    {"id": "B01", "cat": "B", "name": "[정상] 심리상담", "text": "안녕하세요, OO정신건강의학과입니다. 예약하신 비대면 진료 시간 되셔서 연락드렸습니다. 진료 내용에 민감한 개인 정보가 포함될 수 있으니, 지금 주변에 사람이 없는 조용한 방이나 독립된 공간으로 이동해 주실 수 있나요? 카페나 공공장소시면 진료가 어렵습니다. 준비되시면 카카오톡으로 보내드린 '닥터나우(또는 줌)' 링크 눌러서 화상 진료실로 입장해 주세요.", "max": 30, "type": "legitimate"},
    {"id": "B02", "cat": "B", "name": "[정상] 원격지원", "text": "고객님, 말씀하신 와이파이 끊김 현상은 설정 충돌 문제로 보입니다. 제가 고객님 휴대폰 화면을 보면서 설정을 좀 잡아드려야 할 것 같은데요. 휴대폰 기본 설정 메뉴에 보시면 '원격 상담' 기능이 있습니다. 그거 누르시고 화면에 뜨는 6자리 접속 번호를 저한테 불러주시겠어요? 연결되면 제가 화면을 제어하면서 해결해 드리겠습니다.", "max": 30, "type": "legitimate"},
    {"id": "B03", "cat": "B", "name": "[정상] 채용검사", "text": "안녕하세요, OO그룹 인사팀 채용 담당자입니다. 서류 합격 축하드립니다. 내일부터 진행되는 온라인 AI 역량 검사 관련해서 안내 전화 드렸습니다. 부정행위 방지를 위해서 반드시 혼자 계신 공간에서 응시하셔야 하고요, 웹캠으로 주변 360도를 비춰주셔야 합니다. 시험 프로그램은 저희 채용 홈페이지 '마이페이지'에서 다운로드 가능하시니까 미리 설치하고 테스트 부탁드립니다.", "max": 30, "type": "legitimate"},

    # Category C: URL 기반 피싱 (14-23)
    {"id": "C01", "cat": "C", "name": "대법원 위장", "text": "본인 사건이 맞는지 직접 확인해보세요. 인터넷 주소창에 scourt-law.com 입력하시면 대법원 형사 사법 포털 나옵니다. 거기서 '사건 조회' 누르시고 성함 입력해 보세요. 판결문 자세히 보시려면 보안 뷰어(Viewer) 설치하라고 뜨죠? 그거 설치하세요.", "min": 70, "type": "phishing"},
    {"id": "C02", "cat": "C", "name": "검찰청 위장", "text": "바쁘시니까 서울중앙지검 홈페이지(spo-invest.net) 접속하셔서 '비대면 조사실' 배너 클릭하세요. 공인인증서 대신 '수사기관용 본인확인 앱'으로 로그인하셔야 합니다.", "min": 75, "type": "phishing"},
    {"id": "C03", "cat": "C", "name": "금감원 동결", "text": "지금 계좌가 1시간 뒤에 동결됩니다. 금융감독원 민원 포털(fss-secure.co.kr) 들어가셔서 '불법 계좌 해제 신청' 누르세요. 거기서 하라는 대로 보안 프로그램 업데이트하셔야 동결 막습니다.", "min": 75, "type": "phishing"},
    {"id": "C04", "cat": "C", "name": "국세청 환급", "text": "고객님, 국세청입니다. 2024년도 미환급 세액 320만 원이 조회되시는데 신청이 안 되어 있어서요. 모바일 홈택스 주소 보내드릴게요(hometax-refund.info). 여기 접속해서 '환급 신청서' 다운받아 작성해서 다시 올리세요.", "min": 70, "type": "phishing"},
    {"id": "C05", "cat": "C", "name": "건강검진 위장", "text": "건강검진센터입니다. 이번 검사 결과에서 중대한 이상 소견이 발견되어 정밀 검사가 필요합니다. 자세한 수치는 의료 포털(health-check.kr)에서 결과지 조회해 보세요. 결과지 확인 버튼 누르면 의료 정보 암호화 모듈 설치 필요 팝업 뜰 겁니다.", "min": 65, "type": "phishing"},
    {"id": "C06", "cat": "C", "name": "장학금 위장", "text": "한국장학재단입니다. 부모님 소득 정보 오류로 장학금 환수 대상이 되셨어요. 이의 신청하시려면 재단 사이트(kosaf-support.com) 가셔서 증빙 서류 제출 앱을 까셔야 합니다.", "min": 70, "type": "phishing"},
    {"id": "C07", "cat": "C", "name": "대환대출 위장", "text": "정부 지원 '햇살론' 대상자로 선정되셨습니다. 기존 고금리 대출을 3%대로 대환해 드립니다. KB국민은행 특판 사이트(kb-loancenter.net)에서 한도 조회하고 신청 앱 설치하세요.", "min": 65, "type": "phishing"},
    {"id": "C08", "cat": "C", "name": "택배 스미싱", "text": "[CJ대한통운] 운송장 번호 450-*** 주소지 불명으로 반송 대기 중. 실시간 주소지 수정: cj-logistics-help.com 본인 확인을 위해 휴대폰 번호를 입력하고 인증 앱을 설치하세요.", "min": 60, "type": "phishing"},
    {"id": "C09", "cat": "C", "name": "코인 거래소", "text": "업비트 보안팀입니다. 미국에서 로그인이 시도되어 출금이 제한됐습니다. 해제하시려면 전용 보안 페이지(upbit-security.org)에서 OTP 재설정 앱을 다운로드하셔야 합니다.", "min": 70, "type": "phishing"},
    {"id": "C10", "cat": "C", "name": "2차 피해", "text": "사이버수사대입니다. 지난번 신고하신 사기 피해금 찾았습니다. 환급 절차 밟으시려면 경찰청 사이버 안전국(cyber-police.me) 접속하셔서 '피해 구제 신청서' 작성하세요.", "min": 70, "type": "phishing"},

    # Category D: 신규 공격 유형 (24-27)
    {"id": "D01", "cat": "D", "name": "로맨스 스캠", "text": "오빠, 나 오늘 이더리움 선물로 20% 먹었어 ㅋㅋ 저번에 말한 그 AI 매매 프로그램 덕분이야. 내가 쓰는 거래소는 아직 한국에 안 알려진 비공개 거래소(Private Exchange)인데, 레버리지를 100배까지 줘. 오빠도 퀀트 관심 많으니까 내가 초대 코드 줄게. 딱 100만 원만 넣어서 테스트해 봐.", "min": 60, "type": "phishing"},
    {"id": "D02", "cat": "D", "name": "딥보이스 납치", "text": "(울먹이는 목소리로) 아빠! 나 사고 쳤어... 횡단보도에서 사람을 쳤는데 합의금 안 주면 당장 구속된대. 핸드폰도 뺏겼어. 옆에 아저씨 바꿔줄게. (공범 등장) 자녀분이 지금 사람을 크게 다치게 했습니다. 경찰 부르기 전에 조용히 합의 보시죠. 지금 당장 3,000만 원 보내시면 없던 일로 합니다.", "min": 70, "type": "phishing"},
    {"id": "D03", "cat": "D", "name": "부고장 스미싱", "text": "[부고] 모친상. 장례식장: 연세세브란스병원. 바쁘시더라도 참석 부탁드립니다. 약도/모바일 부고장 보기: bit.ly/funeral_kr", "min": 50, "type": "phishing"},
    {"id": "D04", "cat": "D", "name": "고수익 알바", "text": "저희는 법무사 사무실인데요, 세금 문제 때문에 법인 통장을 못 써요. 세영 씨 개인 계좌로 돈을 받아서 저희가 알려주는 계좌로 이체만 해주시면 건당 10만 원 드려요. 혹시 지금 면접 보러 오기 힘드시면, 먼저 업무 테스트부터 해볼게요. 지금 입금된 돈 찾아서 근처 코인 ATM기 가서 송금해 보세요.", "min": 60, "type": "phishing"},

    # Category E: 고난도 애매한 케이스 (28-39)
    # [피싱] 은밀한 원격 제어 유도
    {"id": "E01", "cat": "E", "name": "[피싱] 쿠팡 환불 원격제어", "text": "안녕하세요, 쿠팡 와우 멤버십 고객센터입니다. 정세영 고객님 맞으시죠? 다름이 아니라 시스템 오류로 지난달 멤버십 비용 4,990원이 중복 결제가 되셔서요. 이거 환불 도와드리려고 연락드렸어요. 지금 전산상에서 고객님 단말기 로그가 꼬여있어서 '본인 확인' 버튼이 비활성화되어 있거든요. 플레이스토어에 '팀뷰어' 검색하시면 '퀵 서포트' 앱이 있거든요? 그거 켜서 숫자만 불러주시면 제가 원격으로 접속해서 환불 버튼만 딱 눌러드릴게요.", "min": 75, "type": "phishing"},
    {"id": "E02", "cat": "E", "name": "[피싱] 카드사 FDS팀", "text": "여보세요, 정세영 고객님 되시죠? 여기 OO카드 소비자보호팀입니다. 다름이 아니라 아까 10분 전에 '티몬'에서 98만 원짜리 가전제품 결제 승인이 올라왔는데, 평소 고객님 사용 패턴이랑 달라서 저희 FDS 시스템에서 일단 '보류' 처리를 해뒀거든요. 이거 고객님이 직접 하신 거 맞으실까요? 본인이 아니시다면 이의 제기 신청을 전산상으로 남겨주셔야 최종 취소가 되세요. 제가 지금 문자 하나 보내드렸어요. 그 링크 누르시면 '명의도용 방지 보안관' 앱이 뜨는데, 그거 설치해서 '아니요' 버튼만 한 번 눌러주시면 저희 쪽에서 바로 사건 종결해드릴게요.", "min": 80, "type": "phishing"},
    {"id": "E03", "cat": "E", "name": "[피싱] 대환대출 선입금", "text": "안녕하세요, 정세영 고객님. 여기는 서민금융진흥원 위탁센터입니다. 고객님 지금 00저축은행에서 1,500만 원 쓰고 계신 거 금리가 14.8% 잡혀 있으신데요. 이번에 정부에서 '안심전환대출' 추경 예산이 편성돼서요. 고객님 성실 상환자라 대상자로 선정되셨거든요. 이거 연 3.2% 고정금리로 대환 처리가 가능하세요. 이게 정부 자금이라 중복 수혜가 안 돼요. 그래서 기존 저축은행 대출금을 오늘 오전까지 전액 상환 처리하셔서 전산상 '0'으로 만드셔야 저희 쪽 자금이 실행되거든요. 은행 방문하실 필요 없이 저희가 알려드리는 가상계좌로 상환금 넣으시면 오후 2시에 3.2%짜리 2천만 원 바로 입금됩니다.", "min": 75, "type": "phishing"},
    {"id": "E04", "cat": "E", "name": "[피싱] 병원 수술비 선납", "text": "보호자분 되시죠? 여기 세브란스병원 응급의료센터입니다. 지금 아드님이 전동 킥보드 사고로 이송되셨는데 의식이 혼미합니다. CT상으로 '경막하 출혈' 소견이 보이고요, 왼쪽 대퇴부 복합 골절이라 지금 당장 응급 수술 들어가야 합니다. 골든타임 놓치면 뇌 손상이 올 수 있어요. 지금 사용해야 하는 지혈제랑 인공관절이 '비급여' 품목이라서요. 원무과 접수 전에 이 약재비 450만 원이 먼저 선납이 되어야 약제실에서 불출이 됩니다. 수술 동의서랑 같이 처리해야 하니까 지금 불러드리는 원무과 법인 계좌로 이체하시고 바로 수술실 앞으로 오세요.", "min": 75, "type": "phishing"},
    {"id": "E05", "cat": "E", "name": "[피싱] 로맨스스캠 초기", "text": "어? 이거 김민준 전무님 번호 아닌가요? 골프 모임에서 뵀던... 아이고, 제가 번호를 잘못 저장했나 보네요. 죄송합니다. 목소리가 너무 점잖으셔서 실례인 줄 모르고... 저는 무역 사업 하는 '이수진'이라고 합니다. 이것도 인연인데 혹시 카톡 친구 해도 될까요? 제가 죄송해서 커피 기프티콘이라도 하나 보내드리고 싶어서요.", "min": 65, "type": "phishing"},
    {"id": "E06", "cat": "E", "name": "[피싱] 헤드헌터 사칭", "text": "안녕하세요, 정세영 님 맞으시죠? 여기는 글로벌 헤드헌팅사 '링크드'의 박 부장입니다. 이번에 구글 코리아 퀀트 팀에서 TO가 났는데, 세영 님 깃허브 보고 너무 인상 깊어서 연락드렸어요. 이게 비공개 채용이라 급해서요. 일단 매칭을 위해 주민등록증 사본이랑, 급여 통장 내역서, 그리고 가족 관계 증명서를 지금 바로 제 개인 메일로 좀 보내주시겠어요? 평판 조회 때문에 동의서 작성도 필요한데, 보내드린 URL 눌러서 본인 인증 한번만 해주세요.", "min": 70, "type": "phishing"},

    # [정상] 살벌한 정상 통화
    {"id": "E07", "cat": "E", "name": "[정상] 보험금 지급", "text": "여보세요, 정세영 고객님? 삼성화재 대물보상 담당자입니다. 아까 접수된 접촉 사고 건 때문에 전화드렸어요. 과실 비율 100:0 확정되셨고요. 미수선 수리비로 현금 처리 받으시는 게 유리하실 것 같아서요. 합의금 120만 원 책정되셨는데, 동의하시면 지금 불러주시는 계좌로 바로 송금해드릴게요. 세금 처리 때문에 주민번호 뒷자리도 알려주셔야 합니다.", "max": 30, "type": "legitimate"},
    {"id": "E08", "cat": "E", "name": "[정상] 월세 독촉", "text": "아니, 정세영 씨! 지금 월세가 두 달이나 밀렸는데 전화도 안 받고 뭐 하는 겁니까? 사정이고 뭐고, 오늘 중으로 입금 안 되면 저도 방법 없어요. 내용증명 보내고 명도 소송 걸어서 짐 다 뺄 거니까 알아서 하세요! 당장 송금해요!", "max": 30, "type": "legitimate"},
    {"id": "E09", "cat": "E", "name": "[정상] 경찰서 가족인계", "text": "여보세요? 정세영 씨 핸드폰 맞습니까? 여기 서대문경찰서 신촌지구대 김철수 경위입니다. 놀라지 마시고 들으세요. 지금 아버님 되시는 정OO 님이 길가에 쓰러져 계신 걸 시민분이 신고하셔서 저희가 보호 조치 중입니다. 외상은 없으신데 술을 좀 드신 것 같아요. 지금 바로 지구대로 오셔서 인계해 가셔야 합니다. 오실 때 가족관계 증명할 수 있는 신분증하고 등본 같은 거 챙겨서 오세요. 신촌역 3번 출구 앞 파출소입니다.", "max": 30, "type": "legitimate"},
    {"id": "E10", "cat": "E", "name": "[정상] 중고거래 의심", "text": "저기요, 보내주신 계좌번호 조회해보니까 더치트(사기 조회)에는 안 뜨는데, 제가 불안해서요. 인증 좀 더 해주실 수 있어요? 요즘 벽돌 보내는 사기꾼들이 많아서 그러죠. 혹시 영상통화로 물건 보여주실 수 있어요? 그리고 주민등록증도 가리고 사진 하나만 보내주세요. 확신이 안 서서요. 참나, 5만 원짜리 파는데 무슨 신분증까지 달라 그래요? 됐고요, 정 의심되시면 번개페이(안전결제)로 하시던가요. 수수료는 그쪽이 부담하시고요.", "max": 30, "type": "legitimate"},
    {"id": "E11", "cat": "E", "name": "[정상] 가족 급전 요청", "text": "엄마! 나 지금 큰일 났어. 나 지금 홍대인데 지갑을 잃어버렸어. 집에 갈 차비도 없고 카드도 다 정지시켜서 아무것도 못 해. 어, 폰은 있는데 배터리 3%야. 끊어지면 안 돼. 엄마, 나 지금 친구 계좌로 10만 원만 빨리 보내줘. 내가 집 가서 바로 줄게. 급해 진짜. 어, '박민수'고 카카오뱅크야. 내가 문자로 찍어보낼게. 지금 당장 좀 넣어줘. 나 택시 타야 돼.", "max": 30, "type": "legitimate"},
    {"id": "E12", "cat": "E", "name": "[정상] 투자 사기 항의", "text": "야, 너네가 500% 수익 난다며! 지금 마이너스 40%인데 이게 말이 돼? 당장 환불해줘. 안 그러면 금감원에 신고하고 경찰서 가서 고소장 접수할 거야! 회원님, 진정하시고요. 투자 손실은 본인 책임이라고 약관에 동의하셨잖아요. 웃기지 마. 너네 처음에 가입비 500만 원 입금하면 원금 보장해준다며 녹취 다 있어. 당장 내 계좌로 돈 다시 송금해.", "max": 30, "type": "legitimate"},
]

def main():
    print("\n" + "="*100)
    print("🔬 Gemini Detector + Rule Filter 벤치마크 - 39개 케이스 (고난도 포함)")
    print("="*100)
    print("Category A: 전통적 보이스피싱 (10개)")
    print("Category B: 정상 케이스 (3개)")
    print("Category C: URL 기반 피싱 (10개)")
    print("Category D: 신규 공격 유형 (4개)")
    print("Category E: 고난도 애매한 케이스 (12개) - 피싱 6개, 정상 6개")
    print("="*100 + "\n")

    detector = GeminiPhishingDetector()

    if not detector.is_available():
        print("❌ Gemini API를 사용할 수 없습니다.")
        return

    print("✅ Gemini Phishing Detector 초기화 완료\n")

    all_results = []

    for test_case in test_cases:
        print(f"[{test_case['id']}] {test_case['name']} 테스트 중...", end=" ")

        try:
            result = detector.analyze(test_case["text"], enable_filter=True)

            all_results.append({
                "id": test_case["id"],
                "cat": test_case["cat"],
                "name": test_case["name"],
                "type": test_case["type"],
                "expected_min": test_case.get("min", 0),
                "expected_max": test_case.get("max", 100),
                "score": result.get("score", 0),
                "llm_score": result.get("llm_score", 0),
                "filter_applied": result.get("filter_applied", False),
                "reasoning": result.get("reasoning", "")
            })

            print(f"✅ (점수: {result.get('score', 0)})")
        except Exception as e:
            print(f"❌ 에러: {e}")
            all_results.append({
                "id": test_case["id"],
                "cat": test_case["cat"],
                "name": test_case["name"],
                "type": test_case["type"],
                "expected_min": test_case.get("min", 0),
                "expected_max": test_case.get("max", 100),
                "score": 0,
                "llm_score": 0,
                "filter_applied": False,
                "reasoning": f"Error: {e}"
            })

        time.sleep(1)  # Rate limit

    # 결과 분석
    print("\n" + "="*100)
    print("📊 카테고리별 정답률")
    print("="*100 + "\n")

    categories = {"A": "전통적 보이스피싱", "B": "정상 케이스", "C": "URL 피싱", "D": "신규 유형", "E": "고난도 케이스"}

    for cat_id, cat_name in categories.items():
        print(f"\n[{cat_id}] {cat_name}")
        print("-"*100)

        cat_results = [r for r in all_results if r["cat"] == cat_id]
        correct = 0

        for r in cat_results:
            is_correct = False
            if r["type"] == "legitimate":
                is_correct = r["score"] <= r["expected_max"]
            else:
                is_correct = r["score"] >= r["expected_min"]

            status = "✅" if is_correct else "❌"
            if is_correct:
                correct += 1

            filter_mark = "🔧" if r["filter_applied"] else "  "

            print(f"{status} {filter_mark} [{r['id']}] {r['name']:<20} | "
                  f"기대: {r.get('expected_min', 0):>3}-{r.get('expected_max', 100):<3} | "
                  f"LLM: {r['llm_score']:>3} → 최종: {r['score']:>3}")

        acc = (correct / len(cat_results) * 100) if cat_results else 0
        print(f"\n정답률: {acc:.1f}% ({correct}/{len(cat_results)})")

    # 전체 정답률
    print("\n" + "="*100)
    print("🏆 전체 정답률")
    print("="*100)

    total_correct = 0
    for r in all_results:
        if r["type"] == "legitimate":
            if r["score"] <= r["expected_max"]:
                total_correct += 1
        else:
            if r["score"] >= r["expected_min"]:
                total_correct += 1

    total_acc = (total_correct / len(all_results) * 100) if all_results else 0
    print(f"\nGemini + Rule Filter: {total_acc:.1f}% ({total_correct}/{len(all_results)})")

    # Rule Filter 통계
    filter_count = sum(1 for r in all_results if r["filter_applied"])
    print(f"\nRule Filter 적용: {filter_count}/{len(all_results)} 케이스 ({filter_count/len(all_results)*100:.1f}%)")

    print("\n" + "="*100)
    print("✅ 벤치마크 완료!")
    print("="*100)

if __name__ == "__main__":
    main()
