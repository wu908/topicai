/**
 * Header — V3 design.
 * Minimal top bar. In the V3 prototype, page titles live in PageContainer and
 * the AI call quota badge is folded into the right panel per page. The header
 * is kept as a thin spacer to preserve the protected-route DOM contract.
 */
import React from 'react';

const Header: React.FC = () => {
  return <div style={{ display: 'none' }} aria-hidden="true" />;
};

export default Header;
