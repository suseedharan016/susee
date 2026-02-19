import React, { useState, useEffect } from "react";
import "./NotificationBell.css";

const NotificationBell = ({ t }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await fetch("http://localhost:5000/notifications?limit=10", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:5000/notifications/${notificationId}/read`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        setNotifications((prev) =>
          prev.map((n) => (n.notification_id === notificationId ? { ...n, is_read: true } : n))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem("token");
      setLoading(true);
      const response = await fetch("http://localhost:5000/notifications/read-all", {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        setUnreadCount(0);
      }
    } catch (error) {
      console.error("Failed to mark all as read:", error);
    } finally {
      setLoading(false);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`http://localhost:5000/notifications/${notificationId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setNotifications((prev) =>
          prev.filter((n) => n.notification_id !== notificationId)
        );
        const notification = notifications.find((n) => n.notification_id === notificationId);
        if (notification && !notification.is_read) {
          setUnreadCount((prev) => Math.max(0, prev - 1));
        }
      }
    } catch (error) {
      console.error("Failed to delete notification:", error);
    }
  };

  const formatTimeAgo = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return t?.justNow || "Just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}${t?.minutesAgo || "m ago"}`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}${t?.hoursAgo || "h ago"}`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}${t?.daysAgo || "d ago"}`;
    return date.toLocaleDateString();
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case "match":
        return "🎯";
      case "application_update":
        return "📋";
      case "interview":
        return "📅";
      case "deadline":
        return "⏰";
      default:
        return "🔔";
    }
  };

  const getPriorityClass = (priority) => {
    switch (priority) {
      case "urgent":
        return "notification-urgent";
      case "high":
        return "notification-high";
      case "low":
        return "notification-low";
      default:
        return "";
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="notification-bell-container">
      <button
        className="notification-bell"
        onClick={() => setShowDropdown(!showDropdown)}
        aria-label={t?.notifications || "Notifications"}
      >
        <span className="bell-icon">🔔</span>
        {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
      </button>

      {showDropdown && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h3>{t?.notifications || "Notifications"}</h3>
            {unreadCount > 0 && (
              <button
                className="mark-all-read-btn"
                onClick={markAllAsRead}
                disabled={loading}
              >
                {t?.markAllRead || "Mark all read"}
              </button>
            )}
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">
                <span>📭</span>
                <p>{t?.noNotifications || "No notifications yet"}</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.notification_id}
                  className={`notification-item ${
                    !notification.is_read ? "unread" : ""
                  } ${getPriorityClass(notification.priority)}`}
                  onClick={() => !notification.is_read && markAsRead(notification.notification_id)}
                >
                  <div className="notification-icon">
                    {getNotificationIcon(notification.notification_type)}
                  </div>
                  <div className="notification-content">
                    <div className="notification-title">{notification.title}</div>
                    <div className="notification-message">{notification.message}</div>
                    <div className="notification-time">
                      {formatTimeAgo(notification.created_at)}
                    </div>
                  </div>
                  <button
                    className="delete-notification-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteNotification(notification.notification_id);
                    }}
                    aria-label={t?.delete || "Delete"}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>

          {notifications.length > 0 && (
            <div className="notification-footer">
              <a href="/notifications" className="view-all-link">
                {t?.viewAllNotifications || "View all notifications"}
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
