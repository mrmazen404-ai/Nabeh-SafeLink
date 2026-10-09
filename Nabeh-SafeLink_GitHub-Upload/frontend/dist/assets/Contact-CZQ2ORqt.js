import{A as e,H as t,L as n,O as r,U as i,g as a,o,p as s,r as c,t as l,x as u}from"./index-7QKUHXtX.js";import{t as d}from"./Footer-BULUaziC.js";var f=i(t(),1),p=e();function m({activeTab:e,setActiveTab:t}){let{t:i}=r(),[m,h]=(0,f.useState)(`scan_issue`),[g,_]=(0,f.useState)(``),[v,y]=(0,f.useState)(``),[b,x]=(0,f.useState)(``),[S,C]=(0,f.useState)(``),[w,T]=(0,f.useState)(!1),[E,D]=(0,f.useState)(``),[O,k]=(0,f.useState)(null);return(0,p.jsxs)(`div`,{className:`page-wrapper`,children:[(0,p.jsx)(l,{activeTab:e,setActiveTab:t}),(0,p.jsx)(`main`,{className:`main-content`,id:`main-content`,children:(0,p.jsxs)(`div`,{className:`contact-page-container`,children:[(0,p.jsxs)(`nav`,{className:`breadcrumb`,"aria-label":`Breadcrumb`,children:[(0,p.jsx)(`button`,{type:`button`,className:`breadcrumb-link`,onClick:()=>t(`home`),children:i(`nav.breadcrumbHome`)}),(0,p.jsx)(`span`,{className:`breadcrumb-separator`,children:`/`}),(0,p.jsx)(`span`,{className:`breadcrumb-current`,children:i(`nav.contact`)})]}),(0,p.jsxs)(`div`,{className:`contact-header-card`,children:[(0,p.jsx)(`div`,{className:`contact-title-icon`,children:(0,p.jsx)(a,{size:28,color:`var(--color-primary)`})}),(0,p.jsxs)(`div`,{children:[(0,p.jsx)(`h1`,{className:`contact-h1`,children:i(`contact.title`)}),(0,p.jsx)(`p`,{className:`contact-subtitle`,children:i(`contact.subtitle`)})]})]}),(0,p.jsxs)(`div`,{className:`contact-info-card`,children:[(0,p.jsxs)(`div`,{className:`info-card-header`,children:[(0,p.jsx)(a,{size:18,color:`var(--color-secondary)`}),(0,p.jsx)(`h3`,{children:i(`contact.supportCardTitle`)})]}),(0,p.jsxs)(`div`,{className:`info-card-body`,children:[(0,p.jsxs)(`p`,{children:[(0,p.jsx)(`strong`,{children:i(`contact.supportEmailLabel`)}),` `,(0,p.jsx)(`a`,{href:`mailto:support@nabeh-safelink.com`,className:`support-email-link`,children:`support@nabeh-safelink.com`})]}),(0,p.jsx)(`p`,{className:`hours-note`,children:i(`contact.supportHoursLabel`)})]})]}),O?(0,p.jsxs)(`div`,{className:`contact-success-card`,children:[(0,p.jsx)(`div`,{className:`success-icon-badge`,children:(0,p.jsx)(o,{size:48,color:`var(--color-success)`})}),(0,p.jsx)(`h2`,{children:i(`contact.successTitle`)}),(0,p.jsx)(`p`,{className:`success-msg`,children:i(`contact.successMsg`,{ticketId:O})}),(0,p.jsxs)(`div`,{className:`success-actions`,children:[(0,p.jsx)(`button`,{type:`button`,className:`btn-secondary`,onClick:()=>{k(null),y(``),x(``),C(``),D(``)},children:i(`contact.newRequestBtn`)}),(0,p.jsxs)(`button`,{type:`button`,className:`btn-primary`,onClick:()=>t(`faq`),children:[(0,p.jsx)(s,{size:16}),(0,p.jsx)(`span`,{children:i(`contact.backToFaqBtn`)})]})]})]}):(0,p.jsxs)(`form`,{className:`contact-form-card`,onSubmit:async e=>{if(e.preventDefault(),D(``),!g.trim()||!g.includes(`@`)){D(i(`contact.emailLabel`)+` - الرجاء إدخال بريد إلكتروني صحيح`);return}if(!v.trim()){D(i(`contact.subjectLabel`)+` - هذا الحقل مطلوب`);return}if(!S.trim()){D(i(`contact.detailsLabel`)+` - هذا الحقل مطلوب`);return}T(!0);try{let e=await n({requestType:m,email:g.trim(),subject:v.trim(),scanId:b.trim(),details:S.trim()});if(e&&e.success&&e.ticket_id)k(e.ticket_id);else{let e=`TK-`+Math.floor(1e4+Math.random()*9e4);k(e)}}catch{let e=`TK-`+Math.floor(1e4+Math.random()*9e4);k(e)}finally{T(!1)}},noValidate:!0,children:[E&&(0,p.jsxs)(`div`,{className:`form-error-banner`,role:`alert`,children:[(0,p.jsx)(c,{size:18,color:`var(--color-danger)`}),(0,p.jsx)(`span`,{children:E})]}),(0,p.jsxs)(`div`,{className:`form-group`,children:[(0,p.jsx)(`label`,{htmlFor:`requestType`,children:i(`contact.typeLabel`)}),(0,p.jsxs)(`select`,{id:`requestType`,className:`form-control`,value:m,onChange:e=>h(e.target.value),children:[(0,p.jsx)(`option`,{value:`scan_issue`,children:i(`contact.typeScanIssue`)}),(0,p.jsx)(`option`,{value:`inaccurate_result`,children:i(`contact.typeInaccurateResult`)}),(0,p.jsx)(`option`,{value:`account_general`,children:i(`contact.typeAccountGeneral`)}),(0,p.jsx)(`option`,{value:`suggestion`,children:i(`contact.typeSuggestion`)}),(0,p.jsx)(`option`,{value:`other`,children:i(`contact.typeOther`)})]})]}),(0,p.jsxs)(`div`,{className:`form-group`,children:[(0,p.jsx)(`label`,{htmlFor:`contactEmail`,children:i(`contact.emailLabel`)}),(0,p.jsx)(`input`,{id:`contactEmail`,type:`email`,className:`form-control`,placeholder:i(`contact.emailPlaceholder`),value:g,onChange:e=>_(e.target.value),required:!0})]}),(0,p.jsxs)(`div`,{className:`form-group`,children:[(0,p.jsx)(`label`,{htmlFor:`contactSubject`,children:i(`contact.subjectLabel`)}),(0,p.jsx)(`input`,{id:`contactSubject`,type:`text`,className:`form-control`,placeholder:i(`contact.subjectPlaceholder`),value:v,onChange:e=>y(e.target.value),required:!0})]}),(0,p.jsxs)(`div`,{className:`form-group`,children:[(0,p.jsx)(`label`,{htmlFor:`scanId`,children:i(`contact.scanIdLabel`)}),(0,p.jsx)(`input`,{id:`scanId`,type:`text`,className:`form-control`,placeholder:i(`contact.scanIdPlaceholder`),value:b,onChange:e=>x(e.target.value)}),(0,p.jsx)(`span`,{className:`field-hint`,children:i(`contact.scanIdHint`)})]}),(0,p.jsxs)(`div`,{className:`form-group`,children:[(0,p.jsx)(`label`,{htmlFor:`contactDetails`,children:i(`contact.detailsLabel`)}),(0,p.jsx)(`textarea`,{id:`contactDetails`,rows:5,className:`form-control textarea`,placeholder:i(`contact.detailsPlaceholder`),value:S,onChange:e=>C(e.target.value),required:!0})]}),(0,p.jsxs)(`div`,{className:`contact-privacy-alert`,children:[(0,p.jsx)(c,{size:18,color:`var(--color-warning)`}),(0,p.jsx)(`p`,{children:i(`contact.privacyNotice`)})]}),(0,p.jsxs)(`div`,{className:`form-actions`,children:[(0,p.jsx)(`button`,{type:`button`,className:`btn-secondary`,onClick:()=>t(`home`),children:i(`contact.cancelBtn`)}),(0,p.jsx)(`button`,{type:`submit`,className:`btn-primary`,disabled:w,children:w?(0,p.jsx)(`span`,{children:i(`contact.sendingBtn`)}):(0,p.jsxs)(p.Fragment,{children:[(0,p.jsx)(u,{size:16}),(0,p.jsx)(`span`,{children:i(`contact.sendBtn`)})]})})]})]})]})}),(0,p.jsx)(d,{activeTab:e,setActiveTab:t}),(0,p.jsx)(`style`,{children:`
        .page-wrapper {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          background: var(--color-bg);
        }

        .main-content {
          flex: 1;
          padding: var(--space-6, 24px) var(--space-4, 16px);
        }

        .contact-page-container {
          max-width: 720px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: var(--space-5, 20px);
        }

        .breadcrumb {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: var(--color-text-muted);
        }

        .breadcrumb-link {
          background: none;
          border: none;
          padding: 0;
          font-family: inherit;
          font-size: 13px;
          color: var(--color-secondary);
          cursor: pointer;
        }

        .breadcrumb-link:hover {
          text-decoration: underline;
        }

        .contact-header-card {
          display: flex;
          align-items: center;
          gap: var(--space-4, 16px);
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          padding: var(--space-5, 20px);
          box-shadow: var(--shadow-sm);
        }

        .contact-title-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 52px;
          height: 52px;
          background: var(--color-secondary-subtle);
          border-radius: var(--radius-md);
          flex-shrink: 0;
        }

        .contact-h1 {
          font-size: 22px;
          font-weight: 700;
          color: var(--color-text);
          margin: 0 0 4px;
        }

        .contact-subtitle {
          font-size: 14px;
          color: var(--color-text-secondary);
          margin: 0;
          line-height: 1.5;
        }

        .contact-info-card {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          padding: var(--space-4, 16px) var(--space-5, 20px);
        }

        .info-card-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .info-card-header h3 {
          margin: 0;
          font-size: 15px;
          color: var(--color-text);
        }

        .info-card-body p {
          margin: 4px 0;
          font-size: 13px;
          color: var(--color-text-secondary);
        }

        .support-email-link {
          color: var(--color-secondary);
          text-decoration: none;
          font-weight: 600;
        }

        .support-email-link:hover {
          text-decoration: underline;
        }

        .hours-note {
          font-size: 12px;
          color: var(--color-text-muted);
        }

        .contact-form-card {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          padding: var(--space-6, 24px);
          display: flex;
          flex-direction: column;
          gap: var(--space-4, 16px);
          box-shadow: var(--shadow-sm);
        }

        .form-error-banner {
          display: flex;
          align-items: center;
          gap: 10px;
          background: var(--color-danger-subtle);
          border: 1px solid var(--color-danger);
          border-radius: var(--radius-md);
          padding: 10px 14px;
          color: var(--color-danger);
          font-size: 13px;
          font-weight: 500;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-group label {
          font-size: 14px;
          font-weight: 600;
          color: var(--color-text);
        }

        .form-control {
          width: 100%;
          padding: 10px 14px;
          background: var(--color-bg);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          font-family: inherit;
          font-size: 14px;
          color: var(--color-text);
          outline: none;
          transition: border-color var(--transition-fast);
          box-sizing: border-box;
        }

        .form-control:focus {
          border-color: var(--color-secondary);
        }

        .textarea {
          resize: vertical;
          min-height: 100px;
        }

        .field-hint {
          font-size: 12px;
          color: var(--color-text-muted);
        }

        .contact-privacy-alert {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          background: var(--color-warning-subtle);
          border: 1px solid var(--color-warning);
          border-radius: var(--radius-md);
          padding: 12px 14px;
        }

        .contact-privacy-alert p {
          margin: 0;
          font-size: 13px;
          line-height: 1.5;
          color: var(--color-text);
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 8px;
        }

        .btn-primary {
          background: var(--color-primary);
          color: #ffffff;
          border: none;
          padding: 10px 22px;
          border-radius: var(--radius-md);
          font-family: inherit;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        .btn-primary:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: var(--color-bg);
          color: var(--color-text);
          border: 1px solid var(--color-border);
          padding: 10px 20px;
          border-radius: var(--radius-md);
          font-family: inherit;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
        }

        .contact-success-card {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          padding: var(--space-8, 48px) var(--space-6, 24px);
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .contact-success-card h2 {
          margin: 0;
          font-size: 20px;
          color: var(--color-text);
        }

        .success-msg {
          margin: 0;
          font-size: 14px;
          color: var(--color-text-secondary);
          max-width: 500px;
          line-height: 1.6;
        }

        .success-actions {
          display: flex;
          gap: 12px;
          margin-top: 8px;
        }

        @media (max-width: 600px) {
          .form-actions {
            flex-direction: column-reverse;
          }
          .btn-primary, .btn-secondary {
            width: 100%;
            justify-content: center;
          }
        }
      `})]})}export{m as default};