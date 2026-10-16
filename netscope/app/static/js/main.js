document.addEventListener('DOMContentLoaded', function () {
  const chartNodes = document.querySelectorAll('[data-chart]');

  chartNodes.forEach(function (node) {
    const config = JSON.parse(node.dataset.chart);
    if (window.Chart) {
      new Chart(node, config);
    }
  });

  document.querySelectorAll('.toast').forEach(function (toastEl) {
    toastEl.classList.remove('show');
    if (window.bootstrap && bootstrap.Toast) {
      new bootstrap.Toast(toastEl, { delay: 5000, autohide: false });
    }
  });

  document.querySelectorAll('.alert').forEach(function (alertBox) {
    setTimeout(function () {
      if (alertBox && alertBox.parentNode) {
        alertBox.remove();
      }
    }, 4000);
  });

  function playNotificationSound() {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) {
        return;
      }
      const context = new AudioContextClass();
      const oscillator = context.createOscillator();
      const gainNode = context.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.value = 880;
      gainNode.gain.value = 0.04;
      oscillator.connect(gainNode);
      gainNode.connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.18);
    } catch (error) {
      console.log('Notification sound unavailable', error);
    }
  }

  const roleButtons = document.querySelectorAll('.role-option');
  const loginRoleInput = document.getElementById('loginRole');
  if (roleButtons.length && loginRoleInput) {
    roleButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        const selectedRole = button.dataset.role;
        loginRoleInput.value = selectedRole;
        roleButtons.forEach(function (item) {
          item.classList.toggle('active', item === button);
        });
      });
    });
  }

  const body = document.body;
  const role = body.dataset.userRole;
  const userId = body.dataset.userId;
  const adminToggle = document.getElementById('adminNotificationToggle');
  const adminPanel = document.getElementById('adminNotificationPanel');
  const adminCountEl = document.getElementById('adminNotificationCount');
  const adminMarkAllReadBtn = document.getElementById('adminMarkAllRead');
  const csrfToken = document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '';

  if (adminPanel) {
    adminPanel.setAttribute('hidden', 'hidden');
    adminPanel.setAttribute('aria-hidden', 'true');
  }

  function formatMessageTime(dateString) {
    if (!dateString) {
      return '';
    }
    const date = new Date(dateString);
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function appendMiniChatMessage(container, message, isMine) {
    if (!container) {
      return;
    }
    const emptyState = container.querySelector('.mini-chat-empty');
    if (emptyState) {
      emptyState.remove();
    }
    const item = document.createElement('div');
    item.className = 'mini-chat-message' + (isMine ? ' mine' : '');
    item.innerHTML = '<span>' + (message.sender_name || 'User') + ':</span><small>' + formatMessageTime(message.created_at) + '</small><div>' + (message.content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>') + '</div>';
    container.appendChild(item);
    container.scrollTop = container.scrollHeight;
  }

  function wireMiniTicketChatForms() {
    document.querySelectorAll('[data-ticket-chat-form]').forEach(function (form) {
      if (form.dataset.wired === 'true') {
        return;
      }
      form.dataset.wired = 'true';
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        const textarea = form.querySelector('textarea');
        const ticketId = form.closest('[data-ticket-id]') ? form.closest('[data-ticket-id]').dataset.ticketId : null;
        const content = (textarea ? textarea.value : '').trim();
        if (!ticketId || !content) {
          return;
        }
        fetch('/tickets/' + ticketId + '/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          body: JSON.stringify({ content: content })
        })
          .then(function (response) {
            if (!response.ok) {
              throw new Error('Unable to send message');
            }
            return response.json();
          })
          .then(function (message) {
            textarea.value = '';
            const container = form.previousElementSibling;
            appendMiniChatMessage(container, message, Number(message.sender_id) === Number(userId));
          })
          .catch(function (error) {
            console.error(error);
          });
      });
    });
  }

  function clearAdminBadge() {
    if (adminCountEl) {
      adminCountEl.remove();
    }
    if (adminPanel) {
      adminPanel.querySelectorAll('.notification-item.unread').forEach(function (item) {
        item.classList.remove('unread');
        const unreadPill = item.querySelector('.notification-new-pill');
        if (unreadPill) {
          unreadPill.remove();
        }
      });
    }
  }

  function setAdminPanelVisible(visible) {
    if (!adminPanel) {
      return;
    }
    if (visible) {
      adminPanel.removeAttribute('hidden');
      adminPanel.setAttribute('aria-hidden', 'false');
    } else {
      adminPanel.setAttribute('hidden', 'hidden');
      adminPanel.setAttribute('aria-hidden', 'true');
    }
  }

  if (adminToggle && adminPanel) {
    adminToggle.addEventListener('click', function () {
      const isHidden = adminPanel.hasAttribute('hidden');
      setAdminPanelVisible(isHidden);

      if (role === 'admin' && userId) {
        fetch('/admin/notifications/read', {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
          body: '{}'
        }).then(function () {
          clearAdminBadge();
        }).catch(function () {});
      }
    });
  }

  if (adminMarkAllReadBtn && role === 'admin' && userId) {
    adminMarkAllReadBtn.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      fetch('/admin/notifications/read', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
        body: '{}'
      }).then(function () {
        clearAdminBadge();
      }).catch(function () {});
    });
  }

  wireMiniTicketChatForms();

  if (window.io) {
    const ticketSocket = io();
    document.querySelectorAll('.ticket-mini-chat').forEach(function (chatBox) {
      const ticketId = chatBox.dataset.ticketId;
      if (!ticketId) {
        return;
      }
      ticketSocket.emit('join_ticket_chat', { ticket_id: Number(ticketId) });
      ticketSocket.on('ticket_message_received', function (message) {
        if (Number(message.ticket_id) !== Number(ticketId)) {
          return;
        }
        const panel = document.querySelector('.ticket-mini-chat[data-ticket-id="' + ticketId + '"] .ticket-mini-chat-messages');
        if (panel) {
          appendMiniChatMessage(panel, message, Number(message.sender_id) === Number(userId));
        }
      });
    });
  }

  if (role === 'admin' && userId && window.io) {
    if (window.__netscopeAdminSocket) {
      window.__netscopeAdminSocket.emit('join_admin', { user_id: Number(userId) });
    } else {
      const socket = io();
      window.__netscopeAdminSocket = socket;
      socket.emit('join_admin', { user_id: Number(userId) });

      socket.on('new_ticket_notification', function (data) {
        if (adminToggle) {
          adminToggle.classList.remove('alerting');
          void adminToggle.offsetWidth;
          adminToggle.classList.add('alerting');
        }

        const count = (adminCountEl ? Number(adminCountEl.textContent.trim()) : 0) + 1;
        if (adminCountEl) {
          adminCountEl.textContent = String(count);
        } else if (adminToggle) {
          const badge = document.createElement('span');
          badge.id = 'adminNotificationCount';
          badge.className = 'notification-count';
          badge.textContent = '1';
          adminToggle.appendChild(badge);
        }

        if (adminPanel && adminPanel.querySelector('.notification-empty')) {
          adminPanel.querySelector('.notification-empty').remove();
        }

        const item = document.createElement('a');
        item.href = data.link;
        item.className = 'notification-item unread';
        item.innerHTML = '<div class="notification-item-header"><span>' + data.message + '</span><span class="notification-new-pill">Unread</span></div><small>Just now</small>';
        if (adminPanel) {
          adminPanel.insertBefore(item, adminPanel.firstChild);
        }
      });
    }
  }
});
