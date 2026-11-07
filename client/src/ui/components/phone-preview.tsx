import type { FC } from "react";
import type { PhonePreviewProps } from "../props/phone-preview-props";

export const PhonePreview: FC<PhonePreviewProps> = ({ contactName, message, footerLink, time }) => (
  <div className="w-67.5 max-w-full mx-auto bg-[#0E1512] rounded-[34px] p-2.5 shadow-lg">
    <div className="bg-[#ECE5DD] dark:bg-[#0B141A] rounded-xl overflow-hidden">
      <div className="bg-[#075E54] dark:bg-[#1F2C34] text-white px-3.5 py-3 flex gap-2.25 items-center text-[13px]">
        <div className="w-7.5 h-7.5 rounded-full bg-[#25D366] text-white grid place-items-center font-bold text-xs">
          {contactName.slice(0, 1).toUpperCase()}
        </div>
        {contactName}
      </div>
      <div className="px-3 py-4 pb-5 min-h-75">
        <div className="bg-white dark:bg-[#1F2C34] text-ink dark:text-[#E9EDEF] rounded-[4px_10px_10px_10px] px-3 py-2.5 text-[13px] shadow-[0_1px_1px_rgba(0,0,0,.12)] max-w-[92%] whitespace-pre-wrap">
          {message}
          {footerLink && (
            <div className="mt-2 border-t border-black/7 pt-1.75 text-[#00A5F4] font-semibold text-center text-[12.5px]">
              {footerLink}
            </div>
          )}
          {time && <div className="text-right text-[10.5px] text-[#8B889C] mt-1.25">{time}</div>}
        </div>
      </div>
    </div>
  </div>
);
