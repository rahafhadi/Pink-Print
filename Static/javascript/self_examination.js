
document.addEventListener("DOMContentLoaded", () => {

    // عناصر الصفحة
    const video = document.getElementById("stepVideo");
    const stepTitle = document.getElementById("stepTitle");
    const stepCounter = document.getElementById("stepCounter");
    const descriptionTitle = document.getElementById("descriptionTitle");
    const stepDescription = document.getElementById("stepDescription");
    const progressFill = document.getElementById("progressFill");

    const prevButton = document.getElementById("prevStep");
    const nextButton = document.getElementById("nextStep");

    const videoCard = document.querySelector(".video-card");
    const completionSection = document.getElementById("completionSection");

    // بيانات الخطوات التسع
    const steps = [
        {
            title: "الخطوة الأولى",
            description:
                "قفي أمام المرآة مع إرخاء ذراعيك بجانب جسمك. لاحظي شكل الثديين والحلمتين والجلد، وانتَبهي لأي تغير جديد في الشكل أو المظهر."
        },
        {
            title: "الخطوة الثانية",
            description:
                "ضعي يديك على منطقة الحوض واضغطي برفق، ثم ميلي بجسمك قليلًا إلى الأمام. لاحظي أي تغير في شكل الثديين أو الحلمتين."
        },
        {
            title: "الخطوة الثالثة",
            description:
                "ارفعي إحدى يديك خلف رأسك وميلي بكتفك إلى الأمام كما يوضح الفيديو. لاحظي أي تغير في شكل الثدي أو الجلد."
        },
        {
            title: "الخطوة الرابعة",
            description:
                "تعرّفي على طريقة فحص الثدي باستخدام أطراف ثلاثة أصابع في حركات دائرية منتظمة، مع تغطية مناطق الثدي المختلفة."
        },
        {
            title: "الخطوة الخامسة",
            description:
                "اتبعي طريقة توزيع الضغط على مناطق الثدي المختلفة كما يوضح الفيديو، مع الانتباه إلى المنطقة خلف الحلمة."
        },
        {
            title: "الخطوة السادسة",
            description:
                "انتبهي إلى منطقة تحت الإبط أثناء الفحص؛ فهي جزء مهم من ملاحظة أي تغيرات جديدة."
        },
        {
            title: "الخطوة السابعة",
            description:
                "انتبهي لأي إفرازات من الحلمة، خاصة الإفرازات الدموية أو التي تظهر تلقائيًا. لا تعصري الحلمة بغرض استحداث إفراز، واطلبي تقييمًا طبيًا عند ملاحظة إفراز غير معتاد."
        },
        {
            title: "الخطوة الثامنة",
            description:
                "استلقي على ظهرك وكرري فحص الثدي كما يوضح الفيديو. يمكن وضع وسادة صغيرة تحت الكتف لتسهيل ملاحظة أنسجة الثدي."
        },
        {
            title: "الخطوة التاسعة",
            description:
                "كرري الفحص على الجانب الآخر، مع اتباع وضعية اليد والأصابع الموضحة في الفيديو."
        }
    ];

    let currentStep = 0;

    // عرض الخطوة الحالية
    function showStep(index) {

        const step = steps[index];

        // إيقاف الفيديو السابق
        video.pause();

        // تحديث النصوص
        stepTitle.textContent = step.title;
        descriptionTitle.textContent = step.title;
        stepDescription.textContent = step.description;

        // تحديث رقم الخطوة
        stepCounter.textContent = `${index + 1} / ${steps.length}`;

        // تحديث شريط التقدم
        const progress = ((index + 1) / steps.length) * 100;
        progressFill.style.width = `${progress}%`;

        // تحميل الفيديو المناسب
        video.src = `/static/videos/${index + 1}.mp4`;
        video.load();

        // زر السابق
        prevButton.disabled = index === 0;

        // تغيير نص زر التالي في آخر خطوة
        nextButton.textContent =
            index === steps.length - 1
                ? "إنهاء الخطوات"
                : "الخطوة التالية";
    }

    // الانتقال للخطوة التالية
    nextButton.addEventListener("click", () => {

        if (currentStep < steps.length - 1) {

            currentStep++;
            showStep(currentStep);

        } else {

            // إظهار شاشة النهاية
            video.pause();
            videoCard.hidden = true;
            completionSection.hidden = false;

        }
    });

    // الرجوع للخطوة السابقة
    prevButton.addEventListener("click", () => {

        if (currentStep > 0) {

            currentStep--;
            showStep(currentStep);

        }
    });

    // بدء الصفحة من الخطوة الأولى
    showStep(currentStep);

});
