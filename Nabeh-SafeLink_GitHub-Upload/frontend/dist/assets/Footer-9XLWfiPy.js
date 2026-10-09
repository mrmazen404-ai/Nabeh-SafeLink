import{A as e,C as t,O as n,R as r,S as i,a,g as o,i as s,k as c,m as l,n as u,p as d}from"./index-D-JrSPSy.js";var f=e(),p={home:`/dashboard`,scan:`/scan`,history:`/history`,stats:`/stats`,faq:`/faq`,guide:`/guide`,contact:`/contact`,about:`/about`,notifications:`/notifications`,alerts:`/settings/alerts`};function m({activeTab:e,setActiveTab:m}){let{t:h,dir:g}=n(),{isGuest:_}=c(),v=r(),y=new Date().getFullYear(),b=e=>{typeof m==`function`&&m(e);let t=p[e]||(_&&e===`home`?`/welcome`:`/scan`);v(t)},x=[{id:`faq`,label:h(`nav.faq`),icon:d},{id:`guide`,label:h(`nav.guide`),icon:a},{id:`contact`,label:h(`nav.contact`),icon:o},{id:`about`,label:h(`nav.about`),icon:l}],S=_?[{id:`scan`,label:h(`nav.scan`),icon:t},{id:`about`,label:h(`nav.about`),icon:l},{id:`guide`,label:h(`nav.guide`),icon:a},{id:`faq`,label:h(`nav.faq`),icon:d}]:[{id:`home`,label:h(`nav.home`),icon:t},{id:`scan`,label:h(`nav.scan`),icon:t},{id:`history`,label:h(`nav.history`),icon:s},{id:`stats`,label:h(`nav.stats`),icon:l}];return(0,f.jsxs)(`footer`,{className:`app-footer`,role:`contentinfo`,dir:g,children:[(0,f.jsxs)(`div`,{className:`footer-container`,children:[(0,f.jsxs)(`div`,{className:`footer-brand-section`,children:[(0,f.jsx)(`button`,{type:`button`,className:`footer-logo-btn`,onClick:()=>b(`home`),"aria-label":h(`nav.goHome`),children:(0,f.jsx)(u,{size:`sm`,showTagline:!1})}),(0,f.jsx)(`p`,{className:`footer-tagline`,children:h(`footer.tagline`)}),(0,f.jsxs)(`div`,{className:`footer-version-badge`,children:[(0,f.jsx)(i,{size:14,color:`#16A34A`}),(0,f.jsx)(`span`,{children:`v1.0.0 MVP Stable`})]})]}),(0,f.jsxs)(`div`,{className:`footer-links-column`,children:[(0,f.jsx)(`h3`,{className:`footer-column-title`,children:h(`footer.supportSection`)}),(0,f.jsx)(`ul`,{className:`footer-links-list`,children:x.map(t=>{let n=t.icon,r=e===t.id;return(0,f.jsx)(`li`,{children:(0,f.jsxs)(`button`,{type:`button`,className:`footer-link-btn ${r?`active`:``}`,onClick:()=>b(t.id),children:[(0,f.jsx)(n,{size:15}),(0,f.jsx)(`span`,{children:t.label})]})},t.id)})})]}),(0,f.jsxs)(`div`,{className:`footer-links-column`,children:[(0,f.jsx)(`h3`,{className:`footer-column-title`,children:h(`footer.quickLinksSection`)}),(0,f.jsx)(`ul`,{className:`footer-links-list`,children:S.map(t=>{let n=t.icon,r=e===t.id;return(0,f.jsx)(`li`,{children:(0,f.jsxs)(`button`,{type:`button`,className:`footer-link-btn ${r?`active`:``}`,onClick:()=>b(t.id),children:[(0,f.jsx)(n,{size:15}),(0,f.jsx)(`span`,{children:t.label})]})},t.id)})})]}),(0,f.jsxs)(`div`,{className:`footer-notice-card`,children:[(0,f.jsxs)(`div`,{className:`notice-card-header`,children:[(0,f.jsx)(i,{size:18,color:`var(--color-secondary)`}),(0,f.jsx)(`span`,{className:`notice-card-title`,children:h(`footer.securityTitle`,`حماية موثوقة`)})]}),(0,f.jsx)(`p`,{className:`footer-notice-text`,children:h(`footer.securityNotice`)})]})]}),(0,f.jsx)(`div`,{className:`footer-bottom-bar`,children:(0,f.jsx)(`p`,{className:`footer-copyright`,children:h(`footer.rights`,{year:y})})}),(0,f.jsx)(`style`,{children:`
        .app-footer {
          background: var(--color-surface, #ffffff);
          border-top: 1px solid var(--color-border);
          margin-top: var(--space-8, 48px);
          padding: 48px 24px 28px;
          color: var(--color-text-secondary);
          font-size: 14px;
        }

        .footer-container {
          max-width: 1280px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 1.4fr 1fr 1fr 1.3fr;
          gap: 32px;
        }

        .footer-brand-section {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 14px;
        }

        [dir="rtl"] .footer-brand-section {
          align-items: flex-start;
        }

        .footer-logo-btn {
          background: none;
          border: none;
          padding: 0;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
        }

        .footer-tagline {
          color: var(--color-text-secondary);
          font-size: 13px;
          line-height: 1.6;
          margin: 0;
          max-width: 280px;
        }

        .footer-version-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 12px;
          background: var(--color-bg);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md, 8px);
          font-size: 12px;
          font-weight: 600;
          color: var(--color-text-muted);
        }

        .footer-links-column {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .footer-column-title {
          font-size: 15px;
          font-weight: 700;
          color: var(--color-primary);
          margin: 0;
        }

        .footer-links-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .footer-link-btn {
          background: none;
          border: none;
          padding: 0;
          font-family: inherit;
          font-size: 13px;
          font-weight: 500;
          color: var(--color-text-secondary);
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: color var(--transition-fast, 0.2s ease), transform var(--transition-fast, 0.2s ease);
        }

        .footer-link-btn:hover,
        .footer-link-btn.active {
          color: var(--color-secondary);
          transform: translateX(dir === 'rtl' ? -3px : 3px);
        }

        .footer-notice-card {
          background: var(--color-bg-subtle, #f8fafc);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg, 12px);
          padding: 18px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .notice-card-header {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .notice-card-title {
          font-size: 13px;
          font-weight: 700;
          color: var(--color-primary);
        }

        .footer-notice-text {
          margin: 0;
          font-size: 12px;
          line-height: 1.65;
          color: var(--color-text-muted);
        }

        .footer-bottom-bar {
          max-width: 1280px;
          margin: 32px auto 0;
          padding-top: 20px;
          border-top: 1px solid var(--color-border);
          text-align: center;
        }

        .footer-copyright {
          margin: 0;
          font-size: 12px;
          font-weight: 500;
          color: var(--color-text-muted);
        }

        @media (max-width: 992px) {
          .footer-container {
            grid-template-columns: 1fr 1fr;
            gap: 28px;
          }
        }

        @media (max-width: 600px) {
          .footer-container {
            grid-template-columns: 1fr;
            gap: 24px;
          }
          .app-footer {
            padding: 36px 16px 88px; /* Extra bottom clearance for mobile bottom nav */
          }
        }
      `})]})}export{m as t};