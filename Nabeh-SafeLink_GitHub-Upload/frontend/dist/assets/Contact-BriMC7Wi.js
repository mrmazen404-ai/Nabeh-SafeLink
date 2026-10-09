import{A as e,H as t,O as n,V as r,g as i,o as a,p as o,r as s,t as c,x as l}from"./index-6oEPOiGZ.js";import{t as u}from"./Footer-0EXluM6V.js";var d=t(r(),1),f=e();function p({activeTab:e,setActiveTab:t}){let{t:r}=n(),[p,m]=(0,d.useState)(`scan_issue`),[h,g]=(0,d.useState)(``),[_,v]=(0,d.useState)(``),[y,b]=(0,d.useState)(``),[x,S]=(0,d.useState)(``),[C,w]=(0,d.useState)(!1),[T,E]=(0,d.useState)(``),[D,O]=(0,d.useState)(null);return(0,f.jsxs)(`div`,{className:`page-wrapper`,children:[(0,f.jsx)(c,{activeTab:e,setActiveTab:t}),(0,f.jsx)(`main`,{className:`main-content`,id:`main-content`,children:(0,f.jsxs)(`div`,{className:`contact-page-container`,children:[(0,f.jsxs)(`nav`,{className:`breadcrumb`,"aria-label":`Breadcrumb`,children:[(0,f.jsx)(`button`,{type:`button`,className:`breadcrumb-link`,onClick:()=>t(`home`),children:r(`nav.breadcrumbHome`)}),(0,f.jsx)(`span`,{className:`breadcrumb-separator`,children:`/`}),(0,f.jsx)(`span`,{className:`breadcrumb-current`,children:r(`nav.contact`)})]}),(0,f.jsxs)(`div`,{className:`contact-header-card`,children:[(0,f.jsx)(`div`,{className:`contact-title-icon`,children:(0,f.jsx)(i,{size:28,color:`var(--color-primary)`})}),(0,f.jsxs)(`div`,{children:[(0,f.jsx)(`h1`,{className:`contact-h1`,children:r(`contact.title`)}),(0,f.jsx)(`p`,{className:`contact-subtitle`,children:r(`contact.subtitle`)})]})]}),(0,f.jsxs)(`div`,{className:`contact-info-card`,children:[(0,f.jsxs)(`div`,{className:`info-card-header`,children:[(0,f.jsx)(i,{size:18,color:`var(--color-secondary)`}),(0,f.jsx)(`h3`,{children:r(`contact.supportCardTitle`)})]}),(0,f.jsxs)(`div`,{className:`info-card-body`,children:[(0,f.jsxs)(`p`,{children:[(0,f.jsx)(`strong`,{children:r(`contact.supportEmailLabel`)}),` `,(0,f.jsx)(`a`,{href:`mailto:support@nabeh-safelink.com`,className:`support-email-link`,children:`support@nabeh-safelink.com`})]}),(0,f.jsx)(`p`,{className:`hours-note`,children:r(`contact.supportHoursLabel`)})]})]}),D?(0,f.jsxs)(`div`,{className:`contact-success-card`,children:[(0,f.jsx)(`div`,{className:`success-icon-badge`,children:(0,f.jsx)(a,{size:48,color:`var(--color-success)`})}),(0,f.jsx)(`h2`,{children:r(`contact.successTitle`)}),(0,f.jsx)(`p`,{className:`success-msg`,children:r(`contact.successMsg`,{ticketId:D})}),(0,f.jsxs)(`div`,{className:`success-actions`,children:[(0,f.jsx)(`button`,{type:`button`,className:`btn-secondary`,onClick:()=>{O(null),v(``),b(``),S(``),E(``)},children:r(`contact.newRequestBtn`)}),(0,f.jsxs)(`button`,{type:`button`,className:`btn-primary`,onClick:()=>t(`faq`),children:[(0,f.jsx)(o,{size:16}),(0,f.jsx)(`span`,{children:r(`contact.backToFaqBtn`)})]})]})]}):(0,f.jsxs)(`form`,{className:`contact-form-card`,onSubmit:e=>{if(e.preventDefault(),E(``),!h.trim()||!h.includes(`@`)){E(r(`contact.emailLabel`)+` - الرجاء إدخال بريد إلكتروني صحيح`);return}if(!_.trim()){E(r(`contact.subjectLabel`)+` - هذا الحقل مطلوب`);return}if(!x.trim()){E(r(`contact.detailsLabel`)+` - هذا الحقل مطلوب`);return}w(!0),setTimeout(()=>{let e=`TK-`+Math.floor(1e4+Math.random()*9e4);w(!1),O(e)},800)},noValidate:!0,children:[T&&(0,f.jsxs)(`div`,{className:`form-error-banner`,role:`alert`,children:[(0,f.jsx)(s,{size:18,color:`var(--color-danger)`}),(0,f.jsx)(`span`,{children:T})]}),(0,f.jsxs)(`div`,{className:`form-group`,children:[(0,f.jsx)(`label`,{htmlFor:`requestType`,children:r(`contact.typeLabel`)}),(0,f.jsxs)(`select`,{id:`requestType`,className:`form-control`,value:p,onChange:e=>m(e.target.value),children:[(0,f.jsx)(`option`,{value:`scan_issue`,children:r(`contact.typeScanIssue`)}),(0,f.jsx)(`option`,{value:`inaccurate_result`,children:r(`contact.typeInaccurateResult`)}),(0,f.jsx)(`option`,{value:`account_general`,children:r(`contact.typeAccountGeneral`)}),(0,f.jsx)(`option`,{value:`suggestion`,children:r(`contact.typeSuggestion`)}),(0,f.jsx)(`option`,{value:`other`,children:r(`contact.typeOther`)})]})]}),(0,f.jsxs)(`div`,{className:`form-group`,children:[(0,f.jsx)(`label`,{htmlFor:`contactEmail`,children:r(`contact.emailLabel`)}),(0,f.jsx)(`input`,{id:`contactEmail`,type:`email`,className:`form-control`,placeholder:r(`contact.emailPlaceholder`),value:h,onChange:e=>g(e.target.value),required:!0})]}),(0,f.jsxs)(`div`,{className:`form-group`,children:[(0,f.jsx)(`label`,{htmlFor:`contactSubject`,children:r(`contact.subjectLabel`)}),(0,f.jsx)(`input`,{id:`contactSubject`,type:`text`,className:`form-control`,placeholder:r(`contact.subjectPlaceholder`),value:_,onChange:e=>v(e.target.value),required:!0})]}),(0,f.jsxs)(`div`,{className:`form-group`,children:[(0,f.jsx)(`label`,{htmlFor:`scanId`,children:r(`contact.scanIdLabel`)}),(0,f.jsx)(`input`,{id:`scanId`,type:`text`,className:`form-control`,placeholder:r(`contact.scanIdPlaceholder`),value:y,onChange:e=>b(e.target.value)}),(0,f.jsx)(`span`,{className:`field-hint`,children:r(`contact.scanIdHint`)})]}),(0,f.jsxs)(`div`,{className:`form-group`,children:[(0,f.jsx)(`label`,{htmlFor:`contactDetails`,children:r(`contact.detailsLabel`)}),(0,f.jsx)(`textarea`,{id:`contactDetails`,rows:5,className:`form-control textarea`,placeholder:r(`contact.detailsPlaceholder`),value:x,onChange:e=>S(e.target.value),required:!0})]}),(0,f.jsxs)(`div`,{className:`contact-privacy-alert`,children:[(0,f.jsx)(s,{size:18,color:`var(--color-warning)`}),(0,f.jsx)(`p`,{children:r(`contact.privacyNotice`)})]}),(0,f.jsxs)(`div`,{className:`form-actions`,children:[(0,f.jsx)(`button`,{type:`button`,className:`btn-secondary`,onClick:()=>t(`home`),children:r(`contact.cancelBtn`)}),(0,f.jsx)(`button`,{type:`submit`,className:`btn-primary`,disabled:C,children:C?(0,f.jsx)(`span`,{children:r(`contact.sendingBtn`)}):(0,f.jsxs)(f.Fragment,{children:[(0,f.jsx)(l,{size:16}),(0,f.jsx)(`span`,{children:r(`contact.sendBtn`)})]})})]})]})]})}),(0,f.jsx)(u,{activeTab:e,setActiveTab:t}),(0,f.jsx)(`style`,{children:`
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
      `})]})}export{p as default};