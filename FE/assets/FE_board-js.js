document.addEventListener('DOMContentLoaded', function () {
    console.log("MDB Board scripts loaded");

    // 파일 업로드 유효성 검사
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            validateFileUpload(this);
        });
    }

    // 게시글 작성 폼 유효성 검사 + 파일 검사 + 업로드 실패 대비 메시지
    const boardForm = document.querySelector('.board-form');
    if (boardForm) {
        boardForm.addEventListener('submit', function (e) {
            // 첨부파일 용량 제한 검사
            if (!validateFileUpload(document.getElementById('file'))) {
                e.preventDefault();
                return false;
            }

            // 제목/내용 등 기본 유효성 검사
            if (!validateBoardForm(this)) {
                e.preventDefault();
                return false;
            }

            // 비정상 업로드 시 사용자에게 경고 표시
            setTimeout(() => {
                const fileInput = document.getElementById('file');
                if (fileInput && fileInput.files.length === 0) {
                    alert("파일 업로드 중 문제가 발생했을 수 있습니다. 첨부파일이 사라진 경우 다시 업로드해주세요.");
                }
            }, 2000);
        });
    }

    // FastAPI 응답 예시 기반으로 위험도 표시
    const riskLevelData = window.riskLevelData || null;
    if (riskLevelData) {
        renderRiskLevel(riskLevelData);
    }

    // 삭제 확인 대화상자
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!confirm('정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // 검색 폼 개선
    const searchForm = document.querySelector('.board-search form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    searchForm.submit();
                }
            });
            highlightSearchTerms();
        }
    }

    // 추가 초기화 함수들
    showMalwareWarnings();
    setupFileDownloadWarnings();
    setupAutoRefresh();
    showUploadProgress();
});

// ✅ 위험도 표시 함수 (백엔드 risk_level 기반)
function renderRiskLevel(response) {
    const riskLevel = response.risk_level;
    const readable = response.risk_level_readable;

    const levelElement = document.getElementById('risk-level');
    if (!levelElement) return;

    levelElement.innerText = readable;

    const classMap = {
        "위험": "malware-status-danger",
        "주의": "malware-status-warning",
        "양호": "malware-status-safe",
        "미분석": "malware-status-pending"
    };

    levelElement.className = '';
    levelElement.classList.add(classMap[riskLevel] || 'malware-status-pending');
}

// ✅ 첨부파일 용량 유효성 검사 함수 (2GB 제한)
function validateFileUpload(input) {
    const maxSizeMB = 2048; // 2GB
    const maxSizeBytes = maxSizeMB * 1024 * 1024;

    const file = input.files[0];
    if (!file) return true;

    if (file.size > maxSizeBytes) {
        alert('첨부파일은 최대 2048MB까지만 업로드할 수 있습니다.');
        input.value = ''; // 파일 선택 초기화
        return false;
    }
    return true;
}
// 게시글 상태 확인 (자동 새로고침 or 실패 시 표시)
function checkPostStatus() {
    const currentUrl = window.location.href;
    const postIdMatch = currentUrl.match(/[?&]id=(\d+)/);

    if (!postIdMatch) return;

    const postId = postIdMatch[1];

    if (typeof mdb_ajax !== 'undefined') {
        fetch(mdb_ajax.ajax_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `action=mdb_check_post_status&post_id=${postId}&nonce=${mdb_ajax.nonce}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 상태 변경되었거나 분석 실패면 새로고침
                if (data.data.status_changed || data.data.status === 'failed') {
                    window.location.reload();
                }
            }
        })
        .catch(error => {
            console.error('게시글 상태 확인 실패:', error);
        });
    }
}

// 자동 새로고침 설정 (검사 중인 게시글이 있는 경우)
function setupAutoRefresh() {
    const pendingElements = document.querySelectorAll('.malware-status-pending, .malware-status-failed');

    if (pendingElements.length > 0) {
        let refreshCount = 0;
        const maxRefresh = 10;

        const interval = setInterval(function () {
            refreshCount++;
            if (refreshCount >= maxRefresh) {
                clearInterval(interval);
                return;
            }
            checkPostStatus();
        }, 30000); // 30초 간격

        window.addEventListener('beforeunload', function () {
            clearInterval(interval);
        });
    }
}