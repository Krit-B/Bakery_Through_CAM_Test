# Bakery_Through_CAM_Test

 ดึงมาจาก Roboflow : BU-detection Project [https://universe.roboflow.com/university-ufvlh/bu_bakery_detection]
 
 Class : 3 Classes, ['cookie', 'croissant', 'donut'] 
 
 Train : 100,200 รอบ 
 
 Confusion Matrix : 
[Will be updated.]
 
 # ปัญหา 
: ภาพที่จับได้ยังไม่ตรงกันกับของจริง อย่าง 'คุ้กกี้'ของจริง คอมจัดให้เป็น 'โดนัท' 
	
: คอมที่ทดสอบมี GPU ไม่เพียงพอให้ใช้ batch ที่มากขึ้นได้ ทำให้ใช้เวลาฝึกโมเดลนี้ค่อนข้างนาน (ใช้ 1 ชั่วโมงครึ่ง ต่อ 1 epoch)
