CREATE TABLE IF NOT EXISTS client_app_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    app_id INT NOT NULL,

    status ENUM('trial', 'active', 'suspended', 'expired') NOT NULL DEFAULT 'trial',

    plan_code VARCHAR(50) NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME NULL,

    is_enabled TINYINT(1) NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    created_by VARCHAR(100) NULL,
    notes VARCHAR(255) NULL,

    CONSTRAINT uq_client_app_subscription UNIQUE (client_id, app_id)
);

CREATE INDEX idx_cas_client_id ON client_app_subscriptions (client_id);
CREATE INDEX idx_cas_app_id ON client_app_subscriptions (app_id);
CREATE INDEX idx_cas_status ON client_app_subscriptions (status);
CREATE INDEX idx_cas_client_app_status ON client_app_subscriptions (client_id, app_id, status);