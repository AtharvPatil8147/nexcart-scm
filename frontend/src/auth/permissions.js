export const ROLE_PERMISSIONS = {
  admin: [
    'dashboard:view','sku:view','sku:create','sku:update','sku:delete','sku:risk_override',
    'disruptions:view','disruptions:manage','disruption_agent:run','signals:view','signals:ingest',
    'nudges:view','nudges:manage','nudge_agent:run','analytics:view','settings:view','settings:manage',
    'users:view','users:create','users:update','users:deactivate','users:assign_role','users:reset_password',
    'audit_logs:view','customers:view','customers:manage',
  ],
  manager: [
    'dashboard:view','sku:view','sku:create','sku:update','sku:risk_override','disruptions:view',
    'disruptions:manage','disruption_agent:run','signals:view','signals:ingest','analytics:view','settings:view',
  ],
  viewer: ['dashboard:view','sku:view','disruptions:view','signals:view','analytics:view'],
};

export function hasPermission(user, permission) {
  if (!user) return false;
  if (Array.isArray(user.permissions) && user.permissions.length) return user.permissions.includes(permission);
  return (ROLE_PERMISSIONS[user.role] || []).includes(permission);
}
