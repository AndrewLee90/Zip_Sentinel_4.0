document.addEventListener('DOMContentLoaded', function () {
    console.log("📊 관리자 JS 로드됨");

    // ✅ 게시글 삭제 확인
    const deleteButtons = document.querySelectorAll('.delete-post');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            const title = this.getAttribute('data-title') || '해당 게시글';
            if (!confirm(`정말로 "${title}"을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) {
                e.preventDefault();
            }
        });
    });

    // ✅ 통계 갱신 함수
    function fetchAndUpdateStats() {
        const statsBox = document.querySelector('.malware-board-admin-stats');
        if (!statsBox) return;

        fetch(mbdAdminStats.ajax_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'action=malware_board_admin_stats'
        })
        .then(response => response.json())
        .then(data => {
            statsBox.innerHTML = `
                <p><strong>전체 게시글 수:</strong> ${data.total_posts}</p>
                <p><strong>위험 게시글:</strong> ${data.danger_posts}</p>
                <p><strong>주의 게시글:</strong> ${data.warning_posts}</p>
                <p><strong>양호 게시글:</strong> ${data.safe_posts}</p>
            `;
            console.log("📈 통계 갱신 성공");
        })
        .catch(error => {
            console.error("📉 통계 갱신 실패:", error);
            statsBox.innerHTML = `<p class="error-message">통계 정보를 불러오는 데 실패했습니다.</p>`;
        });
    }

    // ✅ 페이지 로드 시 1회 실행
    fetchAndUpdateStats();

    // ✅ 자동 갱신 (기본: 5분, data-refresh-interval 속성으로 조절 가능)
    const intervalElement = document.querySelector('[data-refresh-interval]');
    const interval = intervalElement
        ? parseInt(intervalElement.getAttribute('data-refresh-interval')) || 300000
        : 300000;

    setInterval(fetchAndUpdateStats, interval);
});
