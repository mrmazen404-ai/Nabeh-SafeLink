import{A as e,O as t,S as n,a as r,g as i,m as a,n as o,p as s}from"./index-DKqb0kUF.js";var c=e();function l({activeTab:e,setActiveTab:l}){let{t:u}=t(),d=new Date().getFullYear(),f=[{id:`faq`,label:u(`nav.faq`),icon:s},{id:`guide`,label:u(`nav.guide`),icon:r},{id:`contact`,label:u(`nav.contact`),icon:i},{id:`about`,label:u(`nav.about`),icon:a}],p=[{id:`home`,label:u(`nav.home`)},{id:`scan`,label:u(`nav.scan`)},{id:`history`,label:u(`nav.history`)},{id:`stats`,label:u(`nav.stats`)}];return(0,c.jsxs)(`footer`,{className:`app-footer`,role:`contentinfo`,children:[(0,c.jsxs)(`div`,{className:`footer-container`,children:[(0,c.jsxs)(`div`,{className:`footer-brand-section`,children:[(0,c.jsx)(`button`,{type:`button`,className:`footer-logo-btn`,onClick:()=>l(`home`),"aria-label":u(`nav.goHome`),children:(0,c.jsx)(o,{size:`sm`,showTagline:!1})}),(0,c.jsx)(`p`,{className:`footer-tagline`,children:u(`footer.tagline`)}),(0,c.jsxs)(`div`,{className:`footer-version-badge`,children:[(0,c.jsx)(n,{size:14,color:`var(--color-success)`}),(0,c.jsx)(`span`,{children:`v1.0.0 MVP Stable`})]})]}),(0,c.jsxs)(`div`,{className:`footer-links-column`,children:[(0,c.jsx)(`h3`,{className:`footer-column-title`,children:u(`footer.supportSection`)}),(0,c.jsx)(`ul`,{className:`footer-links-list`,children:f.map(t=>{let n=t.icon,r=e===t.id;return(0,c.jsx)(`li`,{children:(0,c.jsxs)(`button`,{type:`button`,className:`footer-link-btn ${r?`active`:``}`,onClick:()=>l(t.id),children:[(0,c.jsx)(n,{size:15}),(0,c.jsx)(`span`,{children:t.label})]})},t.id)})})]}),(0,c.jsxs)(`div`,{className:`footer-links-column`,children:[(0,c.jsx)(`h3`,{className:`footer-column-title`,children:u(`footer.quickLinksSection`)}),(0,c.jsx)(`ul`,{className:`footer-links-list`,children:p.map(t=>{let n=e===t.id;return(0,c.jsx)(`li`,{children:(0,c.jsx)(`button`,{type:`button`,className:`footer-link-btn ${n?`active`:``}`,onClick:()=>l(t.id),children:(0,c.jsx)(`span`,{children:t.label})})},t.id)})})]}),(0,c.jsx)(`div`,{className:`footer-notice-card`,children:(0,c.jsx)(`p`,{className:`footer-notice-text`,children:u(`footer.securityNotice`)})})]}),(0,c.jsx)(`div`,{className:`footer-bottom-bar`,children:(0,c.jsx)(`p`,{className:`footer-copyright`,children:u(`footer.rights`,{year:d})})}),(0,c.jsx)(`style`,{children:`
        .app-footer {
          background: var(--color-surface);
          border-top: 1px solid var(--color-border);
          margin-top: var(--space-8, 48px);
          padding: var(--space-8, 48px) var(--space-4, 16px) var(--space-6, 24px);
          color: var(--color-text-secondary);
          font-size: 14px;
        }

        .footer-container {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr 1.2fr;
          gap: var(--space-6, 24px);
        }

        .footer-brand-section {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: var(--space-3, 12px);
        }

        .footer-logo-btn {
          background: none;
          border: none;
          padding: 0;
          cursor: pointer;
          display: inline-flex;
        }

        .footer-tagline {
          color: var(--color-text-secondary);
          font-size: 13px;
          line-height: 1.5;
          margin: 0;
        }

        .footer-version-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: var(--color-bg);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-full);
          font-size: 12px;
          font-weight: 500;
          color: var(--color-text-muted);
        }

        .footer-links-column {
          display: flex;
          flex-direction: column;
          gap: var(--space-3, 12px);
        }

        .footer-column-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--color-text);
          margin: 0;
        }

        .footer-links-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .footer-link-btn {
          background: none;
          border: none;
          padding: 0;
          font-family: inherit;
          font-size: 13px;
          color: var(--color-text-secondary);
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: color var(--transition-fast);
        }

        .footer-link-btn:hover,
        .footer-link-btn.active {
          color: var(--color-secondary);
        }

        .footer-notice-card {
          background: var(--color-bg);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          padding: var(--space-4, 16px);
          display: flex;
          align-items: center;
        }

        .footer-notice-text {
          margin: 0;
          font-size: 12px;
          line-height: 1.6;
          color: var(--color-text-muted);
        }

        .footer-bottom-bar {
          max-width: 1200px;
          margin: var(--space-6, 24px) auto 0;
          padding-top: var(--space-4, 16px);
          border-top: 1px solid var(--color-border);
          text-align: center;
        }

        .footer-copyright {
          margin: 0;
          font-size: 12px;
          color: var(--color-text-muted);
        }

        @media (max-width: 900px) {
          .footer-container {
            grid-template-columns: 1fr 1fr;
          }
        }

        @media (max-width: 600px) {
          .footer-container {
            grid-template-columns: 1fr;
            gap: var(--space-6, 24px);
          }
          .app-footer {
            padding-bottom: 80px; /* space for mobile bottom nav */
          }
        }
      `})]})}export{l as t};