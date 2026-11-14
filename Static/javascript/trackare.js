
/**
 * بصمة وردية - Pink Print
 * trackare.js - منطق تتبع الفحوصات والتقارير السابقة
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================
    // 1. عناصر DOM الرئيسية
    // =========================================================

    const reportsList = document.getElementById('reportsList');
    const btnLoadMore = document.getElementById('btnLoadMore');
    const btnNewExam = document.getElementById('btnNewExam');

    const newExamModal = document.getElementById('newExamModal');
    const editModal = document.getElementById('editModal');
    const toast = document.getElementById('toast');

    const formNewExam = document.getElementById('formNewExam');
    const formEditExam = document.getElementById('formEditExam');

    const closeBtns = document.querySelectorAll('.modal-close-trigger');
    const emptyState = document.getElementById('emptyState');

    let extraLoaded = false;
    let currentCardToEdit = null;


    // =========================================================
    // 2. تنسيق التاريخ
    // =========================================================

    function formatExamDate(dateString) {
        const date = new Date(dateString + 'T00:00:00');

        return new Intl.DateTimeFormat('ar-EG', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        }).format(date);
    }


    // =========================================================
    // 3. إنشاء كارت فحص مختصر
    // =========================================================

    function createCompactExamCard(exam) {

        const card = document.createElement('div');

        card.className = 'exam-card';
        card.dataset.examId = exam.id;

        const cardTop = document.createElement('div');
        cardTop.className = 'card-top-row';

        const dateInfo = document.createElement('div');
        dateInfo.className = 'date-info';

        const dateGroup = document.createElement('div');
        dateGroup.className = 'date-text-group';

        const dateText = document.createElement('span');
        dateText.className = 'exam-date';
        dateText.textContent = formatExamDate(exam.exam_date);

        const timeText = document.createElement('span');
        timeText.className = 'exam-time';
        timeText.textContent = 'تم التسجيل';

        dateGroup.append(dateText, timeText);
        dateInfo.appendChild(dateGroup);

        const status = document.createElement('span');
        status.className = 'exam-status';
        status.textContent = 'تم التسجيل';

        cardTop.append(dateInfo, status);
        card.appendChild(cardTop);

        return card;
    }


    // =========================================================
    // 4. التحكم في رسالة Empty State
    // =========================================================

    function updateEmptyState() {

        if (!reportsList || !emptyState) return;

        const hasExams = reportsList.querySelector('.exam-card');

        emptyState.style.display = hasExams ? 'none' : '';
    }


    // =========================================================
    // 5. تحديث تمييز آخر فحص مسجل
    // =========================================================

    function refreshLatestCardStatus() {

        const allCards = reportsList.querySelectorAll('.exam-card');

        if (allCards.length === 0) return;

        allCards.forEach((card, index) => {

            const textGroup = card.querySelector('.date-text-group');
            const latestBadge = card.querySelector('.latest-tag');

            if (index === 0) {

                card.classList.add('is-latest');

                if (!latestBadge && textGroup) {

                    const badge = document.createElement('span');

                    badge.className = 'latest-tag';
                    badge.textContent = 'آخر فحص مسجل';

                    textGroup.appendChild(badge);
                }

            } else {

                card.classList.remove('is-latest');

                if (latestBadge) {
                    latestBadge.remove();
                }
            }
        });
    }


    // =========================================================
    // 6. تحميل الفحوصات السابقة من قاعدة البيانات
    // =========================================================

    async function loadPreviousExams() {

        try {

            const response = await fetch('/api/self-exams');
            const result = await response.json();

            if (!response.ok || !result.success) {

                console.error(
                    'Failed to load previous exams:',
                    result.message
                );

                updateEmptyState();
                return;
            }

            // إزالة الكروت القديمة قبل إعادة التحميل
            reportsList.querySelectorAll('.exam-card').forEach(card => {
                card.remove();
            });

            // عرض الفحوصات بالترتيب القادم من قاعدة البيانات
            result.exams.forEach(exam => {

                const card = createCompactExamCard(exam);

                reportsList.appendChild(card);
                attachCardEvents(card);
            });

            refreshLatestCardStatus();
            updateEmptyState();

        } catch (error) {

            console.error('Error loading previous exams:', error);
            updateEmptyState();
        }
    }


    // =========================================================
    // 7. أحداث الكروت
    // =========================================================

    function attachCardEvents(card) {

        // زر عرض التفاصيل إن وجد
        const btnView = card.querySelector('.btn-view-result');
        const resultDrawer = card.querySelector('.exam-result-details');

        if (btnView && resultDrawer) {

            btnView.addEventListener('click', (e) => {

                e.stopPropagation();

                const isExpanded =
                    resultDrawer.classList.contains('expanded');

                resultDrawer.classList.toggle('expanded', !isExpanded);
                btnView.classList.toggle('active', !isExpanded);
            });
        }

        // زر التعديل إن وجد
        const btnEdit = card.querySelector('.btn-edit-result');

        if (btnEdit) {

            btnEdit.addEventListener('click', (e) => {

                e.stopPropagation();

                openEditModal(card);
            });
        }

        // زر الحذف إن وجد
        const btnDelete = card.querySelector('.btn-delete-card');

        if (btnDelete) {

            btnDelete.addEventListener('click', (e) => {

                e.stopPropagation();

                deleteCard(card);
            });
        }
    }


    // =========================================================
    // 8. حذف كارت من الواجهة
    // =========================================================

    function deleteCard(card) {

        if (confirm('هل أنتِ متأكدة من رغبتكِ في حذف هذا التقرير؟')) {

            card.style.transition = 'all 0.35s ease';
            card.style.opacity = '0';
            card.style.transform = 'translateY(15px) scale(0.95)';

            setTimeout(() => {

                card.remove();

                refreshLatestCardStatus();
                updateEmptyState();

                showToast('تم حذف التقرير من العرض');

            }, 350);
        }
    }


    // =========================================================
    // 9. نافذة تعديل النتيجة
    // =========================================================

    function openEditModal(card) {

        currentCardToEdit = card;

        const dateElement = card.querySelector('.exam-date');
        const notesElement = card.querySelector('.result-notes-text');

        const currentNotes = notesElement
            ? notesElement.textContent.trim()
            : '';

        document.getElementById('editDate').value =
            dateElement ? dateElement.textContent.trim() : '';

        document.getElementById('editNotes').value = currentNotes;

        if (editModal) {
            editModal.classList.add('active');
        }
    }


    if (formEditExam) {

        formEditExam.addEventListener('submit', (e) => {

            e.preventDefault();

            if (!currentCardToEdit) return;

            const updatedDate =
                document.getElementById('editDate').value.trim();

            const updatedNotes =
                document.getElementById('editNotes').value.trim();

            // تحديث التاريخ في الواجهة فقط
            if (updatedDate) {

                const dateElement =
                    currentCardToEdit.querySelector('.exam-date');

                if (dateElement) {
                    dateElement.textContent = updatedDate;
                }
            }

            const notesElement =
                currentCardToEdit.querySelector('.result-notes-text');

            if (notesElement && updatedNotes) {
                notesElement.textContent = updatedNotes;
            }

            editModal.classList.remove('active');

            showToast('تم تحديث العرض بنجاح ✓');
        });
    }


    // =========================================================
    // 10. فتح نافذة فحص جديد
    // =========================================================

    if (btnNewExam) {

        btnNewExam.addEventListener('click', () => {

            formNewExam.reset();

            newExamModal.classList.add('active');
        });
    }


    // =========================================================
    // 11. حفظ فحص جديد
    // =========================================================

    formNewExam.addEventListener('submit', async (e) => {

        e.preventDefault();

        const formData = new FormData(formNewExam);

        const rawDate =
            document.getElementById('newExamDateInput').value;

        if (!rawDate) {

            showToast('من فضلك حددي تاريخ الفحص');

            return;
        }

        // تجميع إجابات الفحص
        const observations = {};

        for (const [key, value] of formData.entries()) {

            if (
                key === 'newExamDateInput' ||
                key === 'exam_date' ||
                key === 'newExamNotes' ||
                key === 'general_notes'
            ) {
                continue;
            }

            if (
                typeof value === 'string' &&
                value.trim() !== ''
            ) {
                observations[key] = value.trim();
            }
        }

        const generalNotes =
            document.getElementById('newExamNotes')?.value.trim() || '';


        // إرسال البيانات إلى Flask
        try {

            const response = await fetch('/api/self-exams', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({

                    exam_date: rawDate,
                    observations: observations,
                    notes: generalNotes

                })
            });


            const result = await response.json();


            if (!response.ok || !result.success) {

                showToast(
                    result.message || 'حدث خطأ أثناء حفظ الفحص'
                );

                return;
            }


            // الحصول على ID الفحص المحفوظ
            const savedExamId = result.exam_id;


            // إنشاء كارت مختصر
            const newCard = createCompactExamCard({

                id: savedExamId,
                exam_date: rawDate,
                status: 'recorded'

            });


            // إضافته في بداية القائمة
            reportsList.insertBefore(
                newCard,
                reportsList.firstChild
            );


            // تحديث الكروت ورسالة Empty State
            attachCardEvents(newCard);

            refreshLatestCardStatus();

            updateEmptyState();


            // إغلاق الفورم وإعادة ضبطه
            newExamModal.classList.remove('active');

            formNewExam.reset();

            showToast('تم تسجيل الفحص الجديد بنجاح ✓');


        } catch (error) {

            console.error('Save exam error:', error);

            showToast('تعذر الاتصال بالخادم. حاولي مرة أخرى.');
        }
    });


    // =========================================================
    // 12. إغلاق النوافذ
    // =========================================================

    closeBtns.forEach(btn => {

        btn.addEventListener('click', () => {

            newExamModal.classList.remove('active');

            if (editModal) {
                editModal.classList.remove('active');
            }
        });
    });


    // إغلاق النافذة عند الضغط خارج صندوق المحتوى
    [newExamModal, editModal].forEach(modal => {

        if (!modal) return;

        modal.addEventListener('click', (e) => {

            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });


    // =========================================================
    // 13. تحميل البيانات عند فتح الصفحة
    // =========================================================

    loadPreviousExams();

});
